using System.Diagnostics;

namespace BotSharp.Abstraction.Browsing.Models;

[DebuggerStepThrough]
public class WebPageResponseFilter
{
    public string Url { get; set; } = null!;
    public string[]? QueryParameters { get; set; }

    public string[]? PostData { get; set; }

    /// <summary>
    /// contains, starts, ends, equals
    /// </summary>
    public string UrlMatchPattern { get; set; } = "contains";

    /// <summary>
    /// Handle Content-Type: text/x-component
    /// </summary>
    public Func<string, string>? PartSearch { get; set; } = null;
}
