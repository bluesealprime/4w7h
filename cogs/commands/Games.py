import discord 
from discord.ext import commands 
import os 
from core import Cog,AcpXZ,Context 
from utils.Tools import *



class Games (Cog ):
    """AcpXZ Games"""

    def __init__ (self,client:AcpXZ ):
        self.client =client
