using BotSharp.Abstraction.Messaging;
using BotSharp.Abstraction.Messaging.Models.RichContent;
using BotSharp.Abstraction.Options;

namespace BotSharp.Core.Conversations.Services;

public class ConversationStorage : IConversationStorage
{
    private readonly BotSharpOptions _options;
    private readonly IServiceProvider _services;

    public ConversationStorage(
        BotSharpOptions options,
        IServiceProvider services)
    {
        _services = services;
        _options = options;
    }

    public void Append(string conversationId, RoleDialogModel dialog)
    {
        Append(conversationId, [dialog]);
    }

    public void Append(string conversationId, IEnumerable<RoleDialogModel> dialogs)
    {
        if (dialogs.IsNullOrEmpty()) return;

        var db = _services.GetRequiredService<IBotSharpRepository>();
        var dialogElements = new List<DialogElement>();

        foreach ( var dialog in dialogs)
        {
            if (dialog.Role == AgentRole.Function)
            {
                var meta = new DialogMetaData
                {
                    Role = dialog.Role,
                    AgentId = dialog.CurrentAgentId,
                    MessageId = dialog.MessageId,
                    MessageType = dialog.MessageType,
                    FunctionName = dialog.FunctionName,
                    CreatedTime = dialog.CreatedAt
                };

                var content = dialog.Content.RemoveNewLine();
                if (string.IsNullOrEmpty(content))
                {
                    continue;
                }
                dialogElements.Add(new DialogElement
                {
                    MetaData = meta,
                    Content = dialog.Content,
                    SecondaryContent = dialog.SecondaryContent,
                    Payload = dialog.Payload
                });
            }
            else
            {
                var meta = new DialogMetaData
                {
                    Role = dialog.Role,
                    AgentId = dialog.CurrentAgentId,
                    MessageId = dialog.MessageId,
                    MessageType = dialog.MessageType,
                    SenderId = dialog.SenderId,
                    FunctionName = dialog.FunctionName,
                    CreatedTime = dialog.CreatedAt
                };

                var content = dialog.Content.RemoveNewLine();
                if (string.IsNullOrEmpty(content))
                {
                    continue;
                }

                var richContent = dialog.RichContent != null ? JsonSerializer.Serialize(dialog.RichContent, _options.JsonSerializerOptions) : null;
                var secondaryRichContent = dialog.SecondaryRichContent != null ? JsonSerializer.Serialize(dialog.SecondaryRichContent, _options.JsonSerializerOptions) : null;
                dialogElements.Add(new DialogElement
                {
                    MetaData = meta,
                    Content = dialog.Content,
                    SecondaryContent = dialog.SecondaryContent,
                    RichContent = richContent,
                    SecondaryRichContent = secondaryRichContent,
                    Payload = dialog.Payload
                });
            }
        }

        db.AppendConversationDialogs(conversationId, dialogElements);
    }

    public List<RoleDialogModel> GetDialogs(string conversationId)
    {
        var db = _services.GetRequiredService<IBotSharpRepository>();
        var dialogs = db.GetConversationDialogs(conversationId);
        var hooks = _services.GetServices<IConversationHook>();

        var results = new List<RoleDialogModel>();
        foreach (var dialog in dialogs)
        {
            var meta = dialog.MetaData;
            var content = dialog.Content;
            var secondaryContent = dialog.SecondaryContent;
            var payload = string.IsNullOrEmpty(dialog.Payload) ? null : dialog.Payload;
            var role = meta.Role;
            var currentAgentId = meta.AgentId;
            var messageId = meta.MessageId;
            var messageType = meta.MessageType;
            var function = meta.FunctionName;
            var senderId = role == AgentRole.Function ? currentAgentId : meta.SenderId;
            var createdAt = meta.CreatedTime;
            var richContent = !string.IsNullOrEmpty(dialog.RichContent) ? 
                                JsonSerializer.Deserialize<RichContent<IRichMessage>>(dialog.RichContent, _options.JsonSerializerOptions) : null;
            var secondaryRichContent = !string.IsNullOrEmpty(dialog.SecondaryRichContent) ?
                                JsonSerializer.Deserialize<RichContent<IRichMessage>>(dialog.SecondaryRichContent, _options.JsonSerializerOptions) : null;

            var record = new RoleDialogModel(role, content)
            {
                CurrentAgentId = currentAgentId,
                MessageId = messageId,
                MessageType = messageType,
                CreatedAt = createdAt,
                SenderId = senderId,
                FunctionName = function,
                RichContent = richContent,
                SecondaryContent = secondaryContent,
                SecondaryRichContent = secondaryRichContent,
                Payload = payload
            };
            results.Add(record);

            foreach(var hook in hooks)
            {
                hook.OnDialogRecordLoaded(record).Wait();
            }
        }

        foreach (var hook in hooks)
        {
            hook.OnDialogsLoaded(results).Wait();
        }

        return results;
    }
}
