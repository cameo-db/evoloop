"""Tests never read a site file of the machine they run on."""
import os

os.environ["EVOLOOP_SITE"] = "none"
