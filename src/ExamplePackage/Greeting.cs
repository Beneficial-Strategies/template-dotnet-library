namespace BeneficialStrategies.Iso20022;

/// <summary>A placeholder type that keeps the template building. Replace it with the types of the package.</summary>
public static class Greeting
{
    /// <summary>The greeting for a name.</summary>
    /// <param name="name">Who is greeted; it must not be empty.</param>
    /// <returns>A greeting that names <paramref name="name"/>.</returns>
    public static string For(string name)
    {
        if (string.IsNullOrWhiteSpace(name))
            throw new ArgumentException("A name is needed.", nameof(name));
        return $"Hello, {name}.";
    }
}
