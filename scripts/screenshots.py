"""Capture README screenshots from the running stack (docker compose up). Real UI, no mocks."""
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "http://localhost:3000"
OUT = Path(__file__).resolve().parent.parent / "docs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1320, "height": 900})
    pg.goto(URL); pg.wait_for_selector("nav button")
    pg.screenshot(path=OUT / "01-console-offline.png", full_page=True)
    pg.click("button:text-is('Run agent')"); pg.wait_for_selector(".result.notrun")
    pg.screenshot(path=OUT / "02-run-not-configured.png", full_page=True)
    pg.click("nav button:has-text('geo_validator')"); pg.click("main button:text-is('Validate')"); pg.wait_for_selector("pre.okbox")
    pg.locator("main textarea").nth(1).fill('{"city": "Paris"}'); pg.click("main button:text-is('Validate')"); pg.wait_for_selector("pre.badbox")
    pg.screenshot(path=OUT / "03-schema-validation.png", full_page=True)
    pg.click("nav button:has-text('llm_auditor')"); pg.click("button:text-is('Apply callback')"); pg.wait_for_selector("pre.okbox")
    pg.screenshot(path=OUT / "04-auditor-pipeline-callback.png", full_page=True)
    pg.goto("http://localhost:8000/docs"); pg.wait_for_selector(".opblock")
    pg.screenshot(path=OUT / "05-api-docs.png", full_page=True)
    b.close()
print("ok")
