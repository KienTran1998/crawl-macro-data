from crawl4ai import BrowserConfig
import inspect

print("Fields in BrowserConfig:")
print(inspect.signature(BrowserConfig.__init__))
print("\nDocstring:")
print(BrowserConfig.__doc__)
