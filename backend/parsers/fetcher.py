from __future__ import annotations

import logging

from bs4 import BeautifulSoup
import httpx

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


async def fetch_url_text(url: str) -> str:
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(20),
            follow_redirects=True,
            headers=HEADERS,
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            html = resp.text
    except httpx.HTTPStatusError as e:
        logger.warning("HTTP error fetching %s: %s", url, e.response.status_code)
        return ""
    except (httpx.RequestError, Exception) as e:
        logger.warning("Network error fetching %s: %s", url, e)
        return ""

    text = _clean_html(html)

    if len(text.strip()) < 400:
        logger.info(
            "Static fetch yielded short content (%d chars), trying Playwright fallback",
            len(text),
        )
        playwright_text = await _fetch_playwright(url)
        if playwright_text and len(playwright_text) > len(text):
            return playwright_text

    return text


async def _fetch_playwright(url: str) -> str:
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.warning("Playwright not installed — returning static content only")
        return ""

    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, timeout=30000, wait_until="domcontentloaded")
            text = await page.inner_text("body")
            await browser.close()
            return text.strip()
    except Exception:
        logger.exception("Playwright fallback failed")
        return ""


def _clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator="\n")
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    return "\n".join(chunk for chunk in chunks if chunk)
