import enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, ForeignKey, CheckConstraint, UniqueConstraint, Integer, String, Date, Boolean, Enum, DateTime
from sqlalchemy.orm import relationship, backref
from functools import total_ordering

Base = declarative_base()

@total_ordering
class MatchPeriod(enum.Enum):
    upcoming = 0
    pre_match = 1
    first_half = 2
    interval = 3
    second_half = 4
    preparing_extra_time = 5
    extra_first_half = 6
    extra_interval = 7
    extra_second_half = 8
    preparing_penalties = 9
    penalties = 10
    post_match = 11
    finished = 12
    
    def is_ongoing(self):
        return self > MatchPeriod.pre_match and self < MatchPeriod.post_match
    
    def is_running(self):
        return self in [MatchPeriod.first_half, MatchPeriod.second_half, MatchPeriod.extra_first_half, MatchPeriod.extra_second_half, MatchPeriod.penalties]
    
    def is_interval(self):
        return self in [MatchPeriod.pre_match, MatchPeriod.interval, MatchPeriod.preparing_extra_time, MatchPeriod.extra_interval, MatchPeriod.preparing_penalties]
    
    def is_finished(self):
        return self == MatchPeriod.post_match or self == MatchPeriod.finished
    
    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented

class SuggestedSort(enum.Enum):
    blank = 0
    confidence = 1
    top = 2
    new = 3
    controversial = 4
    old = 5
    random = 6
    qa = 7

class PreferredSource(enum.Enum):
    ge = 0
    s365 = 1
    sofa = 2

class Sub(Base):
    __tablename__ = 'sub'
    id = Column(Integer, primary_key=True)
    sub_name = Column(String(255), unique=True, nullable=False)
    
    # Whether to create Post-Match/HUB Threads for this sub
    post_match = Column(Boolean(), nullable=False, default=True)
    match_hub = Column(Boolean(), nullable=False, default=False)
    
    # Create the Match Thread x minutes before the match starts
    pre_match_time = Column(Integer, CheckConstraint('pre_match_time>=0'), nullable=False, default=60)
    
    # Thread Titles
    match_title = Column(String(500), nullable=False, default="[Match Thread] {Campeonato}: {Mandante} x {Visitante}")
    post_title = Column(String(500), nullable=False, default="[Post-Match Thread] {Campeonato}: {Mandante} {PlacarMandante} x {PlacarVisitante} {Visitante}")
    hub_title = Column(String(500), nullable=False, default="[Match HUB] Jogos do dia {Data}")
    
    # Flair for threads
    match_flair = Column(String(255))
    post_match_flair = Column(String(255))
    hub_flair = Column(String(255))
    
    # Whether to pin threads
    pin_match = Column(Boolean(), nullable=False, default=False)
    pin_post = Column(Boolean(), nullable=False, default=False)
    pin_hub = Column(Boolean(), nullable=False, default=False)
    
    # How many hours to wait to unpin the thread
    unpin_match = Column(Integer, CheckConstraint('unpin_match>=0'), nullable=False, default=0)
    unpin_post = Column(Integer, CheckConstraint('unpin_post>=0'), nullable=False, default=12)
    unpin_hub = Column(Integer, CheckConstraint('unpin_hub>=0'), nullable=False, default=0)
    
    # Templates for threads
    match_template = Column(Integer, nullable=False, default=0)
    post_template = Column(Integer, nullable=False, default=0)
    hub_template = Column(Integer, nullable=False, default=0)
    
    # Comments Suggested Sorting for threads
    match_sort = Column(Enum(SuggestedSort), nullable=False, default=SuggestedSort.new)
    post_sort = Column(Enum(SuggestedSort), nullable=False, default=SuggestedSort.new)
    hub_sort = Column(Enum(SuggestedSort), nullable=False, default=SuggestedSort.new)
    
    # Site and Language preferences for Match Thread contents
    preferred_source = Column(Enum(PreferredSource), nullable=False, default=PreferredSource.ge)
    source_language = Column(String(15), nullable=False, default="pt-br")
    instructions_link = Column(String(500))
    
    # Whether to create a detailed play log for matches
    detailed_log = Column(Boolean(), nullable=False, default=True)
    
    # Whether to post Match Stats as a comment during Half Time
    half_time_stats = Column(Boolean(), nullable=False, default=True)
    
    # Other Stuff
    mod_only_request = Column(Boolean(), nullable=False, default=False)
    locked = Column(Boolean(), nullable=False, default=False)
    
    def __repr__(self):
        return "<Sub (sub_name='{}', pre_match_time='{}', match_flair={})>"\
                .format(self.sub_name, self.pre_match_time, self.match_flair)

class Follow(Base):
    __tablename__ = "follow"
    __table_args__ = (
        CheckConstraint('coalesce(team, tour) is not null'),
    )
    id = Column(Integer, primary_key=True)
    sub = Column(Integer, ForeignKey("sub.id", ondelete="CASCADE"), nullable=False)
    team = Column(String(255))
    tour = Column(String(255))
    last_used = Column(DateTime)
    __table_args__ = (UniqueConstraint('sub', 'team', 'tour', name='_sub_team_tour_uc'), )
    parent = relationship('Sub', backref=backref('Follow', passive_deletes=True))
    
    def __repr__(self):
        return "<Follow (sub='{}', team='{}', tour='{}')>"\
                .format(self.sub, self.team, self.tour)

class Match(Base):
    __tablename__ = "match"
    id = Column(Integer, primary_key=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    home_team = Column(String(255), nullable=False)
    away_team = Column(String(255), nullable=False)
    tournament = Column(String(255), nullable=False)
    score = Column(String(255))
    ge_url = Column(String(500))
    s365_url = Column(String(500))
    sofa_url = Column(String(500))
    match_state = Column(Enum(MatchPeriod), nullable=False, default=MatchPeriod.upcoming)
    last_stats_period = Column(Enum(MatchPeriod), nullable=False, default=MatchPeriod.upcoming)
    postponed = Column(Boolean(), nullable=False, default=False)
    post_match_updates = Column(Integer, nullable=False, default=12)
    __table_args__ = (UniqueConstraint('start_time', 'home_team', "away_team", "tournament", name='unique_match_key'), )
    
    def __repr__(self):
        return "<Match (home_team='{}', away_team='{}', tournament={}, date={})>"\
                .format(self.home_team, self.away_team, self.tournament, self.start_time)

class Thread(Base):
    __tablename__ = "thread"
    id = Column(Integer, primary_key=True)
    sub = Column(Integer, ForeignKey("sub.id"), nullable=False)
    match_id = Column(Integer, ForeignKey("match.id", ondelete="CASCADE"), nullable=False)
    url = Column(String(500))
    creation_time = Column(DateTime, nullable=False)
    state = Column(Enum(MatchPeriod), nullable=False, default=MatchPeriod.upcoming)
    post_match_thread = Column(String(500))
    __table_args__ = (UniqueConstraint('sub', 'match_id', name='unique_thread_key'), )
    parent = relationship('Match', backref=backref('Thread', passive_deletes=True))
    
    def __repr__(self):
        return "<Thread (sub='{}', match_id='{}', state={}, url={})>"\
                .format(self.sub, self.match_id, self.state, self.url)

class Hub(Base):
    __tablename__ = "hub"
    id = Column(Integer, primary_key=True)
    sub = Column(Integer, ForeignKey("sub.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    url = Column(String(500))
    parent = relationship('Sub', backref=backref('Hub', passive_deletes=True))

class Request(Base):
    __tablename__ = "request"
    id = Column(Integer, primary_key=True)
    thread = Column(Integer, ForeignKey("thread.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    alert = Column(Boolean(), nullable=False, default=True)
    __table_args__ = (UniqueConstraint('name', 'thread', name='unique_request_key'), )
    parent = relationship('Thread', backref=backref('Request', passive_deletes=True))
    
class PendingUnpin(Base):
    __tablename__ = "unpin"
    id = Column(Integer, primary_key=True)
    url = Column(String(500), nullable=False)
    date = Column(DateTime, nullable=False)

class UnsentPM(Base):
    __tablename__ = "unsent_pm"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    message = Column(String(10000), nullable=False)
