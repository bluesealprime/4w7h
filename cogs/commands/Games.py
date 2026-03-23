import discord 
from discord.ext import commands 
import os 
from core import Cog,Yuna,Context 
from utils.Tools import *



class Games (Cog ):
    """Yuna Games"""

    def __init__ (self,client:Yuna ):
        self.client =client
