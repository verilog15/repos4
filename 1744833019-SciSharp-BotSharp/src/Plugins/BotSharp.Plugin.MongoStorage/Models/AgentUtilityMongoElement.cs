using BotSharp.Abstraction.Agents.Models;

namespace BotSharp.Plugin.MongoStorage.Models;

[BsonIgnoreExtraElements(Inherited = true)]
public class AgentUtilityMongoElement
{
    public string Name { get; set; } = default!;
    public bool Disabled { get; set; }
    public List<UtilityFunctionMongoElement> Functions { get; set; } = [];
    public List<UtilityTemplateMongoElement> Templates { get; set; } = [];

    public static AgentUtilityMongoElement ToMongoElement(AgentUtility utility)
    {
        return new AgentUtilityMongoElement
        {
            Name = utility.Name,
            Disabled = utility.Disabled,
            Functions = utility.Functions?.Select(x => new UtilityFunctionMongoElement(x.Name))?.ToList() ?? [],
            Templates = utility.Templates?.Select(x => new UtilityTemplateMongoElement(x.Name))?.ToList() ?? []
        };
    }

    public static AgentUtility ToDomainElement(AgentUtilityMongoElement utility)
    {
        return new AgentUtility
        {
            Name = utility.Name,
            Disabled = utility.Disabled,
            Functions = utility.Functions?.Select(x => new UtilityFunction(x.Name))?.ToList() ?? [],
            Templates = utility.Templates?.Select(x => new UtilityTemplate(x.Name))?.ToList() ?? []
        };
    }
}

public class UtilityFunctionMongoElement(string name)
{
    public string Name { get; set; } = name;
}

public class UtilityTemplateMongoElement(string name)
{
    public string Name { get; set; } = name;
}