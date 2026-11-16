# Optional Appium setup

The built-in ADB workflow is sufficient for basic interaction. Add Appium when you need semantic selectors, richer assertions, or a reusable UI test suite.

## Install

Requirements: Node.js, a booted Android emulator, and Android SDK Platform-Tools.

```bash
npm install --global appium
appium driver install uiautomator2
appium
```

In another terminal:

```bash
python -m pip install Appium-Python-Client
```

## Minimal Python session

Replace the package ID with your application ID:

```python
from appium import webdriver
from appium.options.android import UiAutomator2Options

options = UiAutomator2Options()
options.platform_name = "Android"
options.automation_name = "UiAutomator2"
options.device_name = "local-avd"
options.udid = "emulator-5554"
options.app_package = "com.example.app"
options.no_reset = True

driver = webdriver.Remote("http://127.0.0.1:4723", options=options)
try:
    print(driver.page_source)
    driver.save_screenshot("artifacts/appium-screen.png")
finally:
    driver.quit()
```

Prefer accessibility IDs and resource IDs over coordinates. Keep Appium bound to localhost unless you have deliberately secured remote access. Appium is optional; this project does not bundle or launch an Appium server automatically.
