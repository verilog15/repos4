using BotSharp.Abstraction.Agents;
using BotSharp.Abstraction.Agents.Enums;
using BotSharp.Abstraction.Loggers;

namespace BotSharp.Plugin.SparkDesk.Providers;

public class ChatCompletionProvider : IChatCompletion
{
    public string Provider => "sparkdesk";
    public string Model => _model;

    private readonly SparkDeskSettings _settings;
    private readonly IServiceProvider _services;
    private readonly ILogger _logger;
    private List<string> renderedInstructions = [];
    private string _model;

    public ChatCompletionProvider(IServiceProvider services,
       SparkDeskSettings settings,
       ILogger<ChatCompletionProvider> logger)
    {
        _services = services;
        _settings = settings;
        _logger = logger;
        _model = $"general{settings.ModelVersion}";
    }


    public async Task<RoleDialogModel> GetChatCompletions(Agent agent, List<RoleDialogModel> conversations)
    {
        var contentHooks = _services.GetServices<IContentGeneratingHook>().ToList();

        // Before chat completion hook
        foreach (var hook in contentHooks)
        {
            await hook.BeforeGenerating(agent, conversations);
        }

        var client = new SparkDeskClient(appId: _settings.AppId, apiKey: _settings.ApiKey, apiSecret: _settings.ApiSecret); 
        var (prompt, messages, funcall) = PrepareOptions(agent, conversations);
        
        var response = await client.ChatAsync(modelVersion:_settings.ModelVersion, messages,functions: funcall.Length == 0 ? null : funcall);

        var responseMessage = new RoleDialogModel(AgentRole.Assistant, response.Text)
        {
            CurrentAgentId = agent.Id,
            MessageId = conversations.Last().MessageId,
            RenderedInstruction = string.Join("\r\n", renderedInstructions)
        };

        if (response.FunctionCall != null)
        {
            responseMessage = new RoleDialogModel(AgentRole.Function, response.Text)
            {
                CurrentAgentId = agent.Id,
                MessageId = conversations.Last().MessageId,
                FunctionName = response.FunctionCall.Name,
                FunctionArgs = response.FunctionCall.Arguments,
                RenderedInstruction = string.Join("\r\n", renderedInstructions)
            };
           
        }

        // After chat completion hook
        foreach (var hook in contentHooks)
        {
            await hook.AfterGenerated(responseMessage, new TokenStatsModel
            {
                Prompt = prompt,
                Provider = Provider,
                Model = _model,
                PromptCount = response.Usage.PromptTokens,
                CompletionCount = response.Usage.CompletionTokens
            });
        }

        return responseMessage;
    }

 

    public async Task<bool> GetChatCompletionsAsync(Agent agent, List<RoleDialogModel> conversations, Func<RoleDialogModel, Task> onMessageReceived, Func<RoleDialogModel, Task> onFunctionExecuting)
    {
        var hooks = _services.GetServices<IContentGeneratingHook>().ToList();

        // Before chat completion hook
        foreach (var hook in hooks)
        {
            await hook.BeforeGenerating(agent, conversations);
        }

        var client = new SparkDeskClient(appId: _settings.AppId, apiKey: _settings.ApiKey, apiSecret: _settings.ApiSecret);
        var (prompt, messages, funcall) = PrepareOptions(agent, conversations);

        var response = await client.ChatAsync(modelVersion: _settings.ModelVersion, messages, functions: funcall.Length == 0 ?null: funcall);

        var msg = new RoleDialogModel(AgentRole.Assistant, response.Text)
        {
            CurrentAgentId = agent.Id,
            RenderedInstruction = string.Join("\r\n", renderedInstructions)
        };

        // After chat completion hook
        foreach (var hook in hooks)
        {
            await hook.AfterGenerated(msg, new TokenStatsModel
            {
                Prompt = prompt,
                Provider = Provider,
                Model = _model,
                PromptCount = response.Usage.PromptTokens,
                CompletionCount = response.Usage.CompletionTokens
            });
        }

        if (response.FunctionCall != null)
        {
            _logger.LogInformation($"[{agent.Name}]: {response.FunctionCall.Name}({response.FunctionCall.Arguments})");

            var funcContextIn = new RoleDialogModel(AgentRole.Function, response.Text)
            {
                CurrentAgentId = agent.Id,
                FunctionName = response.FunctionCall.Name,
                FunctionArgs = response.FunctionCall.Arguments,
                RenderedInstruction = string.Join("\r\n", renderedInstructions)
            };

            // Somethings LLM will generate a function name with agent name.
            if (!string.IsNullOrEmpty(funcContextIn.FunctionName))
            {
                funcContextIn.FunctionName = funcContextIn.FunctionName.Split('.').Last();
            }

            // Execute functions
            await onFunctionExecuting(funcContextIn);
        }
        else
        {
            // Text response received
            await onMessageReceived(msg);
        }

        return true;
    }

    public async Task<bool> GetChatCompletionsStreamingAsync(Agent agent, List<RoleDialogModel> conversations, Func<RoleDialogModel, Task> onMessageReceived)
    {
        var client = new SparkDeskClient(appId: _settings.AppId, apiKey: _settings.ApiKey, apiSecret: _settings.ApiSecret);
        var (prompt, messages, funcall) = PrepareOptions(agent, conversations);

        await foreach (StreamedChatResponse response in client.ChatAsStreamAsync(modelVersion: _settings.ModelVersion, messages, functions: funcall.Length == 0 ? null : funcall))
        {
            if (response.FunctionCall !=null)
            {
                await onMessageReceived(new RoleDialogModel(AgentRole.Function, response.Text) 
                { 
                    CurrentAgentId = agent.Id,
                    FunctionName = response.FunctionCall.Name,
                    FunctionArgs = response.FunctionCall.Arguments,
                    RenderedInstruction = string.Join("\r\n", renderedInstructions)
                });
                continue;
            }

            await onMessageReceived(new RoleDialogModel(AgentRole.Assistant, response.Text)
            {
                CurrentAgentId = agent.Id,
                RenderedInstruction = string.Join("\r\n", renderedInstructions)
            });
 
        } 

        return true;
    }

    public void SetModelName(string model)
    {
        _model = model;
    }

    private (string, ChatMessage[], FunctionDef[]?) PrepareOptions(Agent agent, List<RoleDialogModel> conversations)
    {
        var functions = new List<FunctionDef>();
        var agentService = _services.GetRequiredService<IAgentService>();
        var messages = new List<ChatMessage>();
        renderedInstructions = [];

        if (!string.IsNullOrEmpty(agent.Instruction) || !agent.SecondaryInstructions.IsNullOrEmpty())
        {
            var instruction = agentService.RenderedInstruction(agent);
            renderedInstructions.Add(instruction);
            messages.Add(ChatMessage.FromSystem(instruction));
        }
        if (!string.IsNullOrEmpty(agent.Knowledges))
        {
            messages.Add(ChatMessage.FromSystem(agent.Knowledges));
        }
        var samples = ProviderHelper.GetChatSamples(agent.Samples);
        foreach (var message in samples)
        {
            messages.Add(message.Role == AgentRole.User ?
                ChatMessage.FromUser(message.Content) :
                ChatMessage.FromAssistant(message.Content));
        }

        var agentFuncs = agent.Functions.Concat(agent.SecondaryFunctions ?? []);
        foreach (var function in agentFuncs)
        {
            functions.Add(ConvertToFunctionDef(function));
        }

        foreach (var message in conversations)
        {
            if (message.Role == "function")
            {
                //messages.Add(ChatMessage.FromUser($"function call result: {message.Content}"));
            }
            else if (message.Role == "user")
            {
                var userMessage = ChatMessage.FromUser(message.Content);

                messages.Add(userMessage);
            }
            else if (message.Role == "assistant")
            {
                messages.Add(ChatMessage.FromAssistant(message.Content));
            }
        }

        var prompt = GetPrompt(messages, functions);
        return  (prompt, messages.ToArray(), functions.ToArray());       
    }

    private string GetPrompt(List<ChatMessage> messages, List<FunctionDef> functions)
    {
        var prompt = string.Empty;

        if (messages.Count > 0)
        {
            // System instruction
            var verbose = string.Join("\r\n", messages
                .Where(x => x.Role == AgentRole.System)
                .Select(x =>
                {
                    return $"{x.Role}: {x.Content}";
                }));
            prompt += $"{verbose}\r\n";

            verbose = string.Join("\r\n", messages
                .Where(x => x.Role != AgentRole.System).Select(x =>
                {
                        return  
                            $"{x.Role}: {x.Content}";
                    
                }));
            prompt += $"\r\n{verbose}\r\n";
        }
        return prompt;
    }

    private FunctionDef ConvertToFunctionDef(BotSharp.Abstraction.Functions.Models.FunctionDef def)
    {
        var parameters = def.Parameters;
        var funcParamsProperties = parameters.Properties;
        var requiredList = parameters.Required;
        var fundef = new List<FunctionParametersDef>();
        if (funcParamsProperties != null)
        {
            var props = funcParamsProperties.RootElement.EnumerateObject();
            while (props.MoveNext())
            {
                var prop = props.Current;
                var name = prop.Name;
                bool required = requiredList.Contains(name);
                FunctionParametersDef parametersDef = new FunctionParametersDef(name, prop.Value.GetProperty("type").GetRawText(), prop.Value.GetProperty("description").GetRawText(), required);
                fundef.Add(parametersDef);
            }
        }
        FunctionDef functionDef = new FunctionDef(def.Name, def.Description, fundef.ToArray());
        return functionDef;
    }
}
