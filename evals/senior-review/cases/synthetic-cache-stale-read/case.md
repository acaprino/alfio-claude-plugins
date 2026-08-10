# Case: synthetic-cache-stale-read (data-integrity)

Synthetic. Materialize into a scratch repo (`profiles/repo.py`), commit, review the diff that added the cache layer.

## Buggy code

```python
# profiles/repo.py
CACHE_TTL = 300

async def get_profile(user_id: str) -> Profile:
    cached = await redis.get(f"profile:{user_id}")
    if cached:
        return Profile.parse_raw(cached)
    profile = await db.profiles.find_one({"_id": user_id})
    await redis.set(f"profile:{user_id}", profile.json(), ex=CACHE_TTL)
    return profile

async def update_email(user_id: str, email: str) -> None:
    await db.profiles.update_one({"_id": user_id}, {"$set": {"email": email}})

async def delete_profile(user_id: str) -> None:
    await db.profiles.delete_one({"_id": user_id})
```

## Ground truth (3 bugs)

| # | Known bug | Expected dimension |
|---|-----------|--------------------|
| 1 | `update_email` never invalidates `profile:{user_id}`: reads serve the old email for up to TTL, and code that just wrote the email cannot read its own write | data-integrity (cache/DB divergence) |
| 2 | `delete_profile` never invalidates the cache: a deleted profile keeps being served as existing for up to TTL | data-integrity |
| 3 | TTL is the only consistency mechanism and is presented as none: no read path distinguishes "fresh" from "possibly 5 minutes stale", so callers treat eventual consistency as strong | data-integrity |

## Scoring notes

- The write-path-vs-cache-key trace is the test: full credit requires naming BOTH un-invalidated write paths, not a generic "cache may be stale".
