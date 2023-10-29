import trueskill
import json
from typing import Any, Dict, List, Self, Type
from discord import ApplicationContext, Member
from sqlalchemy import Float, create_engine, Column, Date, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine("sqlite:///player_data.db", echo=True)
Base = declarative_base()


class Player(Base):
    __tablename__ = "players"

    user_id = Column(String, primary_key=True, nullable=False)

    # Rating info
    tank_mu = Column(Float, nullable=False)
    tank_sigma = Column(Float, nullable=False)
    support_mu = Column(Float, nullable=False)
    support_sigma = Column(Float, nullable=False)
    assassin_mu = Column(Float, nullable=False)
    assassin_sigma = Column(Float, nullable=False)
    offlane_mu = Column(Float, nullable=False)
    offlane_sigma = Column(Float, nullable=False)

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


#     self.rating: trueskill.Rating = trueskill.Rating(init_dict["rating"]["mu"], init_dict["rating"]["sigma"])
# else:
#     self.games_played: int = 0
#     self.games_won: int = 0
#     self.rating = trueskill.Rating()
