from typing import Dict, Self
import trueskill
from sqlalchemy import Engine, Float, create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta
from sqlalchemy.orm import scoped_session, sessionmaker

ENGINE: Engine = create_engine("sqlite:///player_data.db", echo=True)
Base: DeclarativeMeta = declarative_base()


class PlayerData(Base):
    __tablename__ = "players"

    user_id = Column(int, primary_key=True, nullable=False)

    # Rating info
    tank_mu = Column(Float, nullable=False, default=trueskill.MU)
    tank_sigma = Column(Float, nullable=False, default=trueskill.SIGMA)
    support_mu = Column(Float, nullable=False, default=trueskill.MU)
    support_sigma = Column(Float, nullable=False, default=trueskill.SIGMA)
    assassin_mu = Column(Float, nullable=False, default=trueskill.MU)
    assassin_sigma = Column(Float, nullable=False, default=trueskill.SIGMA)
    offlane_mu = Column(Float, nullable=False, default=trueskill.MU)
    offlane_sigma = Column(Float, nullable=False, default=trueskill.SIGMA)

    # Play History Info
    tank_games_played = Column(Integer, nullable=False, default=0)
    tank_games_won = Column(Integer, nullable=False, default=0)
    support_games_played = Column(Integer, nullable=False, default=0)
    support_games_won = Column(Integer, nullable=False, default=0)
    assassin_games_played = Column(Integer, nullable=False, default=0)
    assassin_games_won = Column(Integer, nullable=False, default=0)
    offlane_games_played = Column(Integer, nullable=False, default=0)
    offlane_games_won = Column(Integer, nullable=False, default=0)

    def get_stats(self: Self) -> Dict[str, int | str]:
        """Return a representation of the player's stats."""
        return_dict = {}
        for role in ["tank", "support", "assassin", "offlane"]:
            games_played = getattr(self, f"{role}_games_played")
            games_won = getattr(self, f"{role}_games_won")
            if games_played != 0:
                win_rate = games_won / games_played * 100
            else:
                win_rate = 0
            return_dict[role] = {
                "games_played": games_played,
                "games_won": games_won,
                "win_rate": str(win_rate) + "%",
            }
        return return_dict


Base.metadata.create_all(ENGINE)
Session = sessionmaker(bind=Engine)
session = scoped_session()

#     self.rating: trueskill.Rating = trueskill.Rating(init_dict["rating"]["mu"], init_dict["rating"]["sigma"])
# else:
#     self.games_played: int = 0
#     self.games_won: int = 0
#     self.rating = trueskill.Rating()
