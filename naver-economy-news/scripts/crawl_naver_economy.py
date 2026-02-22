#!/usr/bin/env python3
"""네이버 경제 뉴스 크롤러

네이버 뉴스 경제 섹션(sid=101)의 기사를 list.naver 페이지네이션을 통해
대량으로 크롤링하여 구조화된 마크다운 파일로 저장합니다.

수집 전략:
- list.naver 엔드포인트 (mode=LSD, mid=shm, sid1=101) 사용
- 날짜별 최대 200페이지 페이지네이션
- 최근 24시간 이내 기사만 수집
- 중복 기사 자동 제거 (URL 기준)
"""

import json
import re
import sys
import time
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup

CUTOFF_HOURS = 24
MAX_PAGES = 200

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://news.naver.com/section/101",
}


class NaverNewsScraper:
    def __init__(self):
        self.list_url = "https://news.naver.com/main/list.naver"
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def get_recent_articles(self, hours=CUTOFF_HOURS, max_pages=MAX_PAGES):
        cutoff = datetime.now() - timedelta(hours=hours)
        cutoff_date = cutoff.strftime("%Y%m%d")
        recent_articles = []
        seen_links = set()

        print(f"  최근 {hours}시간 기사 수집 중...")

        for list_date in self._iter_recent_dates(cutoff):
            print(f"  날짜 스캔: {list_date}")
            for page in range(1, max_pages + 1):
                try:
                    params = {
                        "mode": "LSD",
                        "mid": "shm",
                        "sid1": "101",
                        "date": list_date,
                        "page": page,
                    }
                    response = self.session.get(
                        self.list_url, params=params, timeout=15
                    )
                    response.raise_for_status()

                    soup = BeautifulSoup(response.text, "html.parser")
                    batch = self._parse_list_articles(soup, list_date=list_date)

                    if not batch:
                        break

                    page_recent = 0
                    page_old = 0

                    for article in batch:
                        link = article.get("link")
                        if link and link in seen_links:
                            continue
                        if link:
                            seen_links.add(link)

                        article_dt = article.get("datetime_obj")
                        if not article_dt:
                            if list_date < cutoff_date:
                                page_old += 1
                                continue
                            article_dt = cutoff

                        if article_dt >= cutoff:
                            article["datetime"] = article_dt.strftime(
                                "%Y-%m-%d %H:%M"
                            )
                            page_recent += 1
                            recent_articles.append(article)
                        else:
                            page_old += 1

                    print(
                        f"    페이지 {page}: 최근 {page_recent}건, 이전 {page_old}건"
                    )

                    if (
                        page_recent == 0
                        and page_old > 0
                        and list_date == cutoff_date
                    ):
                        print("    → 기준 시간 이전 기사 도달, 중단")
                        break

                    time.sleep(0.3)

                except Exception as exc:
                    print(f"    [오류] 페이지 {page}: {exc}", file=sys.stderr)
                    break

        return recent_articles

    def _parse_list_articles(self, soup, list_date):
        results = []
        items = soup.select(".list_body.newsflash_body li")
        for item in items:
            title_tag = item.select_one("dt:not(.photo) a")
            if not title_tag:
                continue
            link = title_tag.get("href", "")
            if not re.search(r"/article/\d+/\d+", link):
                continue
            summary_tag = item.select_one("span.lede")
            press_tag = item.select_one("span.writing")
            date_tag = item.select_one("span.date")
            date_text = date_tag.get_text(strip=True) if date_tag else ""
            article_dt = self._parse_list_datetime(date_text, list_date)

            results.append(
                {
                    "title": title_tag.get_text(strip=True),
                    "link": link,
                    "summary": (
                        summary_tag.get_text(strip=True) if summary_tag else ""
                    ),
                    "press": (
                        press_tag.get_text(strip=True) if press_tag else ""
                    ),
                    "date": list_date,
                    "time_text": date_text,
                    "datetime_obj": article_dt,
                }
            )
        return results

    def _parse_list_datetime(self, text, list_date):
        if not text:
            return None
        now = datetime.now()
        text = text.strip()
        if text.endswith("분전"):
            minutes = int(text.replace("분전", ""))
            return now - timedelta(minutes=minutes)
        if text.endswith("시간전"):
            hours = int(text.replace("시간전", ""))
            return now - timedelta(hours=hours)
        if text.endswith("일전"):
            days = int(text.replace("일전", ""))
            return now - timedelta(days=days)

        m = re.search(r"(\d{4})\.(\d{2})\.(\d{2})\.", text)
        if m:
            year, month, day = m.groups()
            ymd = f"{year}{month}{day}"
        else:
            ymd = list_date

        tm = re.search(r"(오전|오후)\s*(\d{1,2}):(\d{2})", text)
        if tm:
            ampm, hour_s, minute_s = tm.groups()
            hour = int(hour_s) % 12
            if ampm == "오후":
                hour += 12
            return datetime.strptime(f"{ymd}{hour:02d}{minute_s}", "%Y%m%d%H%M")

        if re.match(r"\d{4}\.\d{2}\.\d{2}\.", text):
            return datetime.strptime(ymd, "%Y%m%d")

        return None

    def _iter_recent_dates(self, cutoff):
        dates = []
        current = datetime.now().date()
        cutoff_date = cutoff.date()
        while current >= cutoff_date:
            dates.append(current.strftime("%Y%m%d"))
            current -= timedelta(days=1)
        return dates


def fetch_article_body(url: str, session: requests.Session) -> str:
    """개별 기사 페이지에서 본문 텍스트 추출."""
    try:
        resp = session.get(url, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
    except requests.RequestException:
        return ""

    selectors = [
        "article#dic_area",
        "div#articleBodyContents",
        "div#newsct_article",
        "div.newsct_article",
        "div#articeBody",
        "div._article_body",
    ]
    body_elem = None
    for sel in selectors:
        body_elem = soup.select_one(sel)
        if body_elem:
            break

    if not body_elem:
        return ""

    for tag in body_elem.find_all(["script", "style", "iframe"]):
        tag.decompose()

    text = body_elem.get_text(separator="\n", strip=True)
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    truncated = "\n".join(lines[:20])
    if len(lines) > 20:
        truncated += "\n..."
    return truncated


def fetch_article_bodies(
    articles: list[dict], session: requests.Session, max_body_fetch: int = 5
) -> None:
    """상위 N개 기사의 본문을 가져옴."""
    for i, article in enumerate(articles):
        if i >= max_body_fetch:
            break
        print(f"  본문 수집: {article['title'][:40]}...")
        body = fetch_article_body(article["link"], session)
        article["body"] = body
        time.sleep(0.2)


def generate_markdown(articles: list[dict], date_str: str) -> str:
    """수집된 기사를 마크다운 형식으로 변환."""
    lines = [
        f"# 네이버 경제 뉴스 ({date_str})",
        "",
        f"> 수집 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"> 총 {len(articles)}개 기사 수집",
        "",
    ]

    for i, art in enumerate(articles, 1):
        lines.append(f"### {i}. {art['title']}")
        meta_parts = []
        if art.get("press"):
            meta_parts.append(f"**{art['press']}**")
        if art.get("datetime"):
            meta_parts.append(art["datetime"])
        elif art.get("time_text"):
            meta_parts.append(art["time_text"])
        if meta_parts:
            lines.append(f"- {' | '.join(meta_parts)}")
        lines.append(f"- 링크: {art['link']}")
        if art.get("summary"):
            lines.append(f"- 요약: {art['summary']}")
        if art.get("body"):
            lines.append("")
            lines.append("<details>")
            lines.append("<summary>본문 미리보기</summary>")
            lines.append("")
            lines.append(art["body"])
            lines.append("")
            lines.append("</details>")
        lines.append("")

    if not articles:
        lines.append("수집된 기사가 없습니다.")
        lines.append("")

    return "\n".join(lines)


def main():
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    output_path = f"/tmp/naver_economy_news_{now.strftime('%Y%m%d')}.md"

    print(f"네이버 경제 뉴스 크롤링 시작 ({date_str})")
    print(f"수집 기준: 최근 {CUTOFF_HOURS}시간 이내 기사")
    print()

    scraper = NaverNewsScraper()
    articles = scraper.get_recent_articles(hours=CUTOFF_HOURS, max_pages=MAX_PAGES)

    print()
    print(f"총 {len(articles)}건 기사 수집 완료 (중복 제거 후)")

    # 상위 기사 본문 수집
    if articles:
        print()
        print("주요 기사 본문 수집 중...")
        fetch_article_bodies(articles, scraper.session, max_body_fetch=10)

    # datetime_obj 제거
    for art in articles:
        art.pop("datetime_obj", None)

    # 마크다운 생성 및 저장
    md_content = generate_markdown(articles, date_str)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    print()
    print(f"결과 저장: {output_path}")
    print("크롤링 완료!")


if __name__ == "__main__":
    main()
