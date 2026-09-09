"""Generate the synthetic test fixtures.

The parsers are tested against invented pages, not captured ones. Blind posts
are written by anonymous people and often name colleagues; committing real
threads to a public repo would republish that, and would contradict this
project's own guidance about not accumulating Blind content.

These fixtures reproduce the structural quirks the parsers actually depend on:
  * a schema.org DiscussionForumPosting carrying the AI `abstract`
  * an RSC payload where each reply ALSO matches the comment regex, so the
    parentCommentId filter is exercised
  * commentCount higher than the schema block's comment list
  * low-content replies, for the noise filter

Run: python tests/fixtures/make_fixtures.py
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path

HERE = Path(__file__).parent


def _compact(obj) -> str:
    """Blind ships minified JSON, and the parsers match on space-free markers."""
    return json.dumps(obj, separators=(",", ":"))
BASE = "https://www.teamblind.com"
COMPANY = "Acme"


def _rsc(payload: str) -> str:
    """Wrap a string the way Next.js ships its RSC chunks."""
    return f"<script>self.__next_f.push([1,{json.dumps(payload)}])</script>"


def _comment(cid, nick, company, date, likes, text, replies=(), parent=0, op=False):
    return {
        "id": cid,
        "parentCommentId": parent,
        "memberNickname": nick,
        "likeCnt": likes,
        "isAuth": "Y",
        "isHiddenCompany": company is None,
        "isLiked": False,
        "recomments": list(replies),
        "recommentsCnt": len(replies),
        "images": [],
        "isOp": op,
        "isCoOp": False,
        "isMine": False,
        "createDate": date,
        "writedAt": f"{date}, 2026",
        "companyId": 42,
        "invisibleToCoworkersCompanyName": None,
        "invisibleToCoworkersCompanyId": None,
        "content": text,
        "contentRaw": text,
        "companyName": company,
    }


def build_post() -> str:
    reply = _comment(2002, "tallpine", "Northwind", "Apr 2", 0,
                     "Is that the same for the Pune office?", parent=2001)
    comments = [
        _comment(2000, "brightkite", "Globex", "Mar 31", 4, "TC?"),
        _comment(2001, "quietfox", "Northwind", "Apr 1", 1,
                 "the wfo policy is enforced orgwide, you can take a few days "
                 "wfh at your manager's discretion", replies=[reply]),
        _comment(2003, "slowriver", "Initech", "Jun 4", 0,
                 "Yes 4 days mandatory and the office culture is open"),
        _comment(2004, "hiddenone", None, "Jun 5", 0, "same question"),
    ]

    forum_posting = {
        "@context": "https://schema.org",
        "@type": "DiscussionForumPosting",
        "headline": "Acme India - office policy",
        "text": "Got an offer at Acme India and want to understand whether the "
                "4-day office policy is strictly enforced.",
        "datePublished": "2026-03-31T12:00:00.000Z",
        "url": f"{BASE}/post/acme-india-office-policy-abcd1234",
        "author": {"@type": "Person", "identifier": "askerone", "name": "askerone"},
        # Deliberately higher than the list below: the real pages truncate here.
        "commentCount": 9,
        "interactionStatistic": {
            "@type": "InteractionCounter",
            "interactionType": {"@type": "LikeAction"},
            "userInteractionCount": 5,
        },
        "abstract": "Commenters say the work-from-office policy at Acme India is "
                    "strictly enforced, with a mandatory four-day requirement, "
                    "though exceptions are possible at a manager's discretion.",
        "comment": [
            {"@type": "Comment", "text": c["content"],
             "datePublished": "2026-04-01T00:00:00.000Z", "comment": [],
             "author": {"@type": "Person", "identifier": c["memberNickname"],
                        "name": c["memberNickname"]},
             "upvoteCount": c["likeCnt"], "commentCount": 0}
            for c in comments[:2]
        ],
    }

    return "\n".join([
        "<!doctype html><html><head>",
        "<title>Acme India - office policy | India - Blind</title>",
        f'<script type="application/ld+json">{_compact(forum_posting)}</script>',
        "</head><body>",
        _rsc('{"postDetail":{"title":"Acme India - office policy","comments":'
             + _compact(comments) + "}}"),
        '<p class="whitespace-pre-wrap">the wfo policy is enforced orgwide</p>',
        "</body></html>",
    ])


def _card(alias, title, channel, channel_label, date, company, nick, preview,
          likes, comments, views) -> str:
    return (
        f'<article data-article-alias="{alias}" data-testid="article-preview-card">'
        f'<div class="absolute inset-0 -z-10">'
        f'<a data-testid="article-preview-click-box" href="/post/{alias}">'
        f'<span class="sr-only">{title}</span></a></div>'
        f'<div class="pointer-events-none"><div class="flex items-center gap-2">'
        f'<a href="/channels/{channel}"><div>{channel_label}</div></a>'
        f'<span title="{date}, 2026">{date}</span>'
        f'<span>{company}</span><span>{nick}</span></div>'
        f'<h3>{title}</h3><p>{preview}</p>'
        f'<div><span>{likes}</span><span>{comments}</span><span>{views}</span>'
        f'</div></div></article>'
    )


def build_company() -> str:
    topics = ["india", "interview", "layoffs", "wlb", "rsu"]
    chips = "".join(
        f'<a href="/company/{COMPANY}/posts/{COMPANY.lower()}-{t}">{t}</a>'
        for t in topics
    )
    pager = "".join(
        f'<a href="/company/{COMPANY}/posts?page={n}">{n}</a>' for n in (1, 2, 3, 47)
    )
    cards = [
        _card("acme-india-office-policy-abcd1234", "Acme India - office policy",
              "india", "India", "Mar 31", "Globex", "askerone",
              "Got an offer at Acme India and want to understand the office policy.",
              5, 9, 1106),
        _card("acme-wlb-thread-efgh5678", "How is WLB at Acme really",
              "tech", "Tech Industry", "Aug 12", "Initech", "slowriver",
              "Considering an offer. Is the on-call rotation as bad as people say?",
              12, 30, 4200),
        _card("looking-for-acme-referral-ijkl9012", "Looking for referrals urgently",
              "tech", "Tech Industry", "Sep 1", "Northwind", "jobhunter",
              "6 yoe backend, please refer me at Acme.", 1, 2, 88),
    ]
    return "\n".join([
        "<!doctype html><html><head><title>Acme Discussions - Blind</title></head>",
        "<body>", chips, pager,
        '<div><span class="font-semibold">1,842</span>'
        '<span class="ml-1">Results</span></div>',
        *cards,
        "</body></html>",
    ])


def main() -> None:
    for name, html in (
        ("acme_post.html.gz", build_post()),
        ("acme_company.html.gz", build_company()),
    ):
        (HERE / name).write_bytes(gzip.compress(html.encode()))
        print(f"wrote {name} ({len(html):,} bytes uncompressed)")


if __name__ == "__main__":
    main()
