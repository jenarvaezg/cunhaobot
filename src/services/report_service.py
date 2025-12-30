from datetime import date, datetime
from models.report import Report
from infrastructure.protocols import (
    PhraseRepository,
    LongPhraseRepository,
    UserRepository,
    InlineUserRepository,
    Repository,
)


class ReportService:
    def __init__(
        self,
        report_repo: Repository[Report],
        phrase_repo: PhraseRepository,
        long_phrase_repo: LongPhraseRepository,
        user_repo: UserRepository,
        inline_user_repo: InlineUserRepository,
    ):
        self.report_repo = report_repo
        self.phrase_repo = phrase_repo
        self.long_repo = long_phrase_repo
        self.user_repo = user_repo
        self.inline_repo = inline_user_repo

    def generate_report(self, report_date: date, chapas: list) -> Report:
        long_phrases = self.long_repo.load_all()
        short_phrases = self.phrase_repo.load_all()
        users = self.user_repo.load_all(ignore_gdpr=True)
        inline_users = self.inline_repo.load_all()

        created_at = datetime.combine(report_date, datetime.min.time())

        # Calcular top phrases del día
        def get_total_daily(p):
            return p.daily_usages + p.audio_daily_usages + p.sticker_daily_usages

        top_long = max(long_phrases, key=get_total_daily).text if long_phrases else ""
        top_short = (
            max(short_phrases, key=get_total_daily).text if short_phrases else ""
        )

        report = Report(
            longs=len(long_phrases),
            shorts=len(short_phrases),
            users=len([u for u in users if not u.is_group]),
            groups=len([u for u in users if u.is_group]),
            inline_users=len(inline_users),
            inline_usages=sum(u.usages for u in inline_users),
            gdprs=len([u for u in users if u.gdpr]),
            chapas=len(chapas),
            top_long=top_long,
            top_short=top_short,
            created_at=created_at,
        )

        self.report_repo.save(report)
        return report
