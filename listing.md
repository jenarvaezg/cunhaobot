I have improved the badge system and added a web profile page:

1.  **Enhanced Profile Display**: The `/profile` command in Telegram now shows descriptions for both earned and pending badges. Users can now see exactly what they need to do to earn each badge.
2.  **Implemented Missing Badges**: Added the logic to verify and award the **"Visionario"** (10 Vision usages) and **"Poeta"** (5 proposed phrases) badges.
3.  **Web Profile Page**: Added a new `/user/{user_id}/profile` page on the web interface showing:
    *   User stats (points, usages, phrases).
    *   Badge collection with progress bars for pending ones.
    *   List of phrases contributed by the user.
    *   "Fun stats" section (prepared for future expansion).
4.  **Bug Fixes**: Fixed an issue in `PhraseDatastoreRepository` where it was looking for `author_id` instead of `user_id`.
5.  **Added Tests**: Created `src/services/badge_service_test.py` and `src/web_profile_test.py` to verify changes.
6.  **Verification**: All tests passed (including existing ones) and code style standards (ruff/ty) were met.
