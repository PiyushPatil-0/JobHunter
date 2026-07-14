"""
Repository layer for Job persistence.
"""

from sqlalchemy import delete
from sqlalchemy import func
from sqlalchemy import select
from datetime import datetime
from datetime import timedelta

from app.database.database import get_session
from app.database.models import Job as JobEntity
from app.database.models import UserNotification as UserNotificationEntity
from app.models.job import Job
from app.models.process_result import ProcessResult
from app.models.repository_statistics import RepositoryStatistics


class JobRepository:

    @staticmethod
    def exists(job_hash: str) -> bool:
        with get_session() as session:
            stmt = select(JobEntity).where(JobEntity.hash == job_hash)
            return session.scalar(stmt) is not None

    @staticmethod
    def save(job: Job) -> int:
        entity = JobEntity(
            hash=job.hash,
            title=job.title,
            company=job.company,
            location=job.location,
            experience=job.experience,
            source=job.source.value,
            employment_type=job.employment_type.value,
            description=job.description,
            url=job.url,
            match_score=0,
            resume_score=0,
            notified=False,
        )

        with get_session() as session:
            session.add(entity)
            session.commit()
            session.refresh(entity)
            return entity.id

    @classmethod
    def process(cls, job: Job) -> ProcessResult:
        if cls.exists(job.hash):
            return ProcessResult(
                inserted=False,
                duplicate=True,
            )

        job_id = cls.save(job)

        return ProcessResult(
            inserted=True,
            duplicate=False,
            job_id=job_id,
        )


    @staticmethod
    def mark_notified(job_hash: str) -> None:
        with get_session() as session:
            stmt = select(JobEntity).where(JobEntity.hash == job_hash)
            entity = session.scalar(stmt)

            if entity is None:
                return

            entity.notified = True
            entity.notification_sent_at = datetime.utcnow()

            session.commit()

    @staticmethod
    def statistics() -> RepositoryStatistics:
        with get_session() as session:
            total = session.query(func.count(JobEntity.id)).scalar() or 0

            notified = (
                session.query(func.count(JobEntity.id))
                .filter(JobEntity.notified.is_(True))
                .scalar()
                or 0
            )

            return RepositoryStatistics(
                total_jobs=total,
                notified_jobs=notified,
                pending_jobs=total - notified,
            )

    @staticmethod
    def cleanup(days: int) -> int:
        """Delete jobs and their per-user delivery records past retention."""
        if days < 1:
            raise ValueError("Job retention must be at least one day.")

        cutoff = datetime.utcnow() - timedelta(days=days)
        expired_hashes = select(JobEntity.hash).where(
            JobEntity.created_at < cutoff
        )

        with get_session() as session:
            session.execute(
                delete(UserNotificationEntity).where(
                    UserNotificationEntity.job_hash.in_(expired_hashes)
                )
            )
            result = session.execute(
                delete(JobEntity).where(JobEntity.created_at < cutoff)
            )
            session.commit()
            return result.rowcount or 0
