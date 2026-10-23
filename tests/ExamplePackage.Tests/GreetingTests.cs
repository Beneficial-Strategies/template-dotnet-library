using Xunit;

namespace BeneficialStrategies.Iso20022;

public class GreetingTests
{
    [Fact]
    public void A_greeting_names_the_person() => Assert.Equal("Hello, Ada.", Greeting.For("Ada"));

    [Fact]
    public void An_empty_name_is_refused() => Assert.Throws<ArgumentException>(() => Greeting.For(" "));
}
