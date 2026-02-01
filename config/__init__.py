# -*- coding: utf-8 -*-
"""Módulo de configuração"""
from .settings import settings
from .database import db_pool, get_connection

__all__ = ['settings', 'db_pool', 'get_connection']
