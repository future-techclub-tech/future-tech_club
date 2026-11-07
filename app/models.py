from datetime import datetime
import hashlib
import hmac
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy import UniqueConstraint
from flask import current_app
from .extensions import db, login_manager

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), nullable=False)
    display_name = db.Column(db.String(150), default="")
    email = db.Column(db.String(150), default="")
    phone = db.Column(db.String(40), default="")
    active = db.Column(db.Boolean, default=True)
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        digest = hmac.new(
            current_app.secret_key.encode(),
            self.password_hash.encode(),
            hashlib.sha256,
        ).hexdigest()
        return f"{self.id}:{digest}"

    @property
    def is_active(self):
        return self.active

class Domain(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)


class JudgeAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    judge_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=False)
    judge = db.relationship("User", backref="judge_assignments")
    team = db.relationship("Team", backref="judge_assignments")
    __table_args__ = (UniqueConstraint("judge_id", "team_id"),)


class MentorTeamAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mentor_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=False)
    mentor = db.relationship("User", backref="mentor_team_assignments")
    team = db.relationship("Team", backref="mentor_assignments")
    __table_args__ = (UniqueConstraint("mentor_id", "team_id"),)


class CoordinatorDomainAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    coordinator_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    domain_id = db.Column(db.Integer, db.ForeignKey("domain.id"), nullable=False)
    coordinator = db.relationship("User", backref="coordinator_domain_assignments")
    domain = db.relationship("Domain", backref="coordinator_assignments")
    __table_args__ = (UniqueConstraint("coordinator_id", "domain_id"),)


class CoordinatorTeamAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    coordinator_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=False)
    coordinator = db.relationship("User", backref="coordinator_team_assignments")
    team = db.relationship("Team", backref="coordinator_assignments")
    __table_args__ = (UniqueConstraint("coordinator_id", "team_id"),)


class LoginAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False, index=True)
    successful = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)


class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_code = db.Column(db.String(10), unique=True, nullable=False)
    name = db.Column(db.String(150), default="")
    domain_id = db.Column(db.Integer, db.ForeignKey("domain.id"))
    leader_name = db.Column(db.String(150), default="")
    department = db.Column(db.String(100), default="")
    year = db.Column(db.String(30), default="")
    email = db.Column(db.String(150), default="")
    phone = db.Column(db.String(40), default="")
    mentor_name = db.Column(db.String(150), default="")
    project_title = db.Column(db.String(200), default="")
    abstract = db.Column(db.Text, default="")
    problem_statement = db.Column(db.Text, default="")
    objectives = db.Column(db.Text, default="")
    technologies = db.Column(db.Text, default="")
    registration_status = db.Column(db.String(30), default="Pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    domain = db.relationship("Domain", backref="teams")

class TeamMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    prn = db.Column(db.String(60), unique=True, nullable=False)
    roll_number = db.Column(db.String(40), default="")
    department = db.Column(db.String(100), default="")
    year = db.Column(db.String(30), default="")
    email = db.Column(db.String(150), default="")
    phone = db.Column(db.String(40), default="")
    attendance_records = db.relationship("Attendance", backref="member", cascade="all, delete-orphan")
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True, nullable=True)
    team = db.relationship("Team", backref="members")
    user = db.relationship("User", backref=db.backref("member_record", uselist=False))


class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey("team_member.id"), nullable=False)
    event_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    marked_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    marked_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (UniqueConstraint("member_id", "event_date"),)


class Evaluation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=False)
    judge_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    problem = db.Column(db.Float, default=0)
    innovation = db.Column(db.Float, default=0)
    implementation = db.Column(db.Float, default=0)
    prototype = db.Column(db.Float, default=0)
    impact = db.Column(db.Float, default=0)
    presentation = db.Column(db.Float, default=0)
    qa = db.Column(db.Float, default=0)
    total = db.Column(db.Float, default=0)
    finalized = db.Column(db.Boolean, default=False)
    approved = db.Column(db.Boolean, default=False, nullable=False)
    approved_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    approved_at = db.Column(db.DateTime)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    team = db.relationship("Team", backref="evaluations")
    judge = db.relationship("User", foreign_keys=[judge_id])
    approver = db.relationship("User", foreign_keys=[approved_by])
    __table_args__ = (UniqueConstraint("team_id", "judge_id"),)

class AdminEvaluation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"), unique=True, nullable=False)
    development = db.Column(db.Float, default=0)
    teamwork = db.Column(db.Float, default=0)
    documentation = db.Column(db.Float, default=0)
    discipline = db.Column(db.Float, default=0)
    feasibility = db.Column(db.Float, default=0)
    total = db.Column(db.Float, default=0)
    finalized = db.Column(db.Boolean, default=False)


class MentorEvaluation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=False)
    mentor_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    development = db.Column(db.Float, default=0)
    teamwork = db.Column(db.Float, default=0)
    documentation = db.Column(db.Float, default=0)
    discipline = db.Column(db.Float, default=0)
    feasibility = db.Column(db.Float, default=0)
    total = db.Column(db.Float, default=0)
    status = db.Column(db.String(20), default="Pending", nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    reviewed_at = db.Column(db.DateTime)
    reviewed_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    team = db.relationship("Team", backref="mentor_evaluations")
    mentor = db.relationship("User", foreign_keys=[mentor_id])
    reviewer = db.relationship("User", foreign_keys=[reviewed_by])
    __table_args__ = (UniqueConstraint("team_id", "mentor_id"),)


class TeamTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=False)
    assignee_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    assigner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    status = db.Column(db.String(20), nullable=False, default="Open")
    due_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    team = db.relationship("Team", backref="tasks")
    assignee = db.relationship("User", foreign_keys=[assignee_id], backref="assigned_tasks")
    assigner = db.relationship("User", foreign_keys=[assigner_id])


class WorkTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    scope = db.Column(db.String(20), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=True, index=True)
    assigner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="", nullable=False)
    due_date = db.Column(db.Date, nullable=True)
    reference_storage_name = db.Column(db.String(255), nullable=True)
    reference_original_name = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    team = db.relationship("Team", backref="work_tasks")
    assigner = db.relationship("User", foreign_keys=[assigner_id])
    assignments = db.relationship(
        "WorkTaskAssignment",
        back_populates="task",
        cascade="all, delete-orphan",
    )


class WorkTaskAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey("work_task.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default="Open")
    deliverable_storage_name = db.Column(db.String(255), nullable=True)
    deliverable_original_name = db.Column(db.String(255), nullable=True)
    submitted_at = db.Column(db.DateTime, nullable=True)
    task = db.relationship("WorkTask", back_populates="assignments")
    user = db.relationship("User", backref="work_task_assignments")
    __table_args__ = (UniqueConstraint("task_id", "user_id"),)


class TaskDeadlineReminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_kind = db.Column(db.String(20), nullable=False)
    task_id = db.Column(db.Integer, nullable=False)
    reminder_date = db.Column(db.Date, nullable=False)
    __table_args__ = (
        UniqueConstraint(
            "task_kind",
            "task_id",
            "reminder_date",
            name="uq_task_deadline_reminder",
        ),
    )


class TeamChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    body = db.Column(db.String(2000), nullable=False, default="")
    attachment_storage_name = db.Column(db.String(255), nullable=True)
    attachment_original_name = db.Column(db.String(255), nullable=True)
    edited_at = db.Column(db.DateTime, nullable=True)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    team = db.relationship("Team", backref="chat_messages")
    sender = db.relationship("User", foreign_keys=[sender_id])
    recipient = db.relationship("User", foreign_keys=[recipient_id])


class AdminChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    body = db.Column(db.String(2000), nullable=False, default="")
    attachment_storage_name = db.Column(db.String(255), nullable=True)
    attachment_original_name = db.Column(db.String(255), nullable=True)
    edited_at = db.Column(db.DateTime, nullable=True)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    sender = db.relationship("User", foreign_keys=[sender_id])
    recipient = db.relationship("User", foreign_keys=[recipient_id])


class Nomination(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=False)
    rank = db.Column(db.Integer, nullable=False)
    published = db.Column(db.Boolean, default=False)
    team = db.relationship("Team", backref="nominations")

class ProjectVideo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    team = db.relationship("Team", backref="videos")


class TeamSubmission(db.Model):
    __table_args__ = (
        UniqueConstraint("team_id", "submission_type", name="uq_team_submission_type"),
    )
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=False)
    submission_type = db.Column(db.String(30), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_name = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    team = db.relationship("Team", backref="submissions")


class Winner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=False)
    published = db.Column(db.Boolean, default=False)
    selected_at = db.Column(db.DateTime, default=datetime.utcnow)
    team = db.relationship("Team", backref="winners")


class DomainResultPublication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    domain_id = db.Column(db.Integer, db.ForeignKey("domain.id"), unique=True, nullable=False)
    published_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    published_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    domain = db.relationship("Domain")


class UserNotification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    read = db.Column(db.Boolean, default=False, nullable=False)
    user = db.relationship("User", backref="notifications")


class CertificateType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    description = db.Column(db.Text, default="")
    active = db.Column(db.Boolean, default=True)


class CertificateTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type_id = db.Column(db.Integer, db.ForeignKey("certificate_type.id"), unique=True, nullable=False)
    event_name = db.Column(db.String(200), nullable=False)
    event_date = db.Column(db.String(80), default="", nullable=False)
    event_venue = db.Column(db.String(200), default="", nullable=False)
    recipient_role = db.Column(db.String(30), nullable=False)
    background_file = db.Column(db.String(255), nullable=False)
    document_file = db.Column(db.String(255), nullable=True)
    positions_json = db.Column(db.Text, default="{}", nullable=False)
    page_width = db.Column(db.Float, default=842, nullable=False)
    page_height = db.Column(db.Float, default=595, nullable=False)
    approved = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    certificate_type = db.relationship("CertificateType", backref=db.backref("template", uselist=False))


class Certificate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    certificate_id = db.Column(db.String(50), unique=True, nullable=False)
    type_id = db.Column(db.Integer, db.ForeignKey("certificate_type.id"), nullable=False)
    recipient_name = db.Column(db.Text, nullable=False)
    recipient_role = db.Column(db.String(80), default="")
    team_code = db.Column(db.String(10), default="")
    user_id = db.Column(db.Integer, nullable=True, index=True)
    file_path = db.Column(db.String(255), nullable=True)
    template_id = db.Column(db.Integer, db.ForeignKey("certificate_template.id"))
    fields_json = db.Column(db.Text, default="{}", nullable=False)
    template_snapshot_json = db.Column(db.Text, default="", nullable=False)
    dispatch_status = db.Column(db.String(20), default="pending", nullable=False)
    dispatched_at = db.Column(db.DateTime, nullable=True)
    issued_at = db.Column(db.DateTime, default=datetime.utcnow)
    type = db.relationship("CertificateType")
    template = db.relationship("CertificateTemplate")

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class SiteSetting(db.Model):
    key = db.Column(db.String(80), primary_key=True)
    value = db.Column(db.Text, nullable=False, default="")


class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    action = db.Column(db.String(200), nullable=False)
    details = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    try:
        account_id, _ = user_id.split(":", 1)
        user = db.session.get(User, int(account_id))
    except (AttributeError, TypeError, ValueError):
        return None
    if user and user.active and hmac.compare_digest(user.get_id(), user_id):
        return user
    return None
