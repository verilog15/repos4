namespace BotSharp.Abstraction.Evaluations.Models;

public class SimulationResult
{
    [JsonPropertyName("generated_message")]
    public string GeneratedMessage { get; set; }

    [JsonPropertyName("stop_conversation")]
    public bool Stop { get; set; }

    [JsonPropertyName("reason")]
    public string? Reason { get; set; }
}
