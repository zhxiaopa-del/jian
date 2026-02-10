#!/usr/bin/env python3
"""
数据库模型定义
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Numeric,
    DateTime,
    Text,
    ForeignKey,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()


class CollectionRecord(Base):
    """回款记录表"""
    __tablename__ = "collection_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # 基本信息
    responsible_person = Column(String(100), nullable=False, comment="负责人")
    project_type = Column(String(100), nullable=False, comment="项目类型")
    project_name = Column(String(200), nullable=False, comment="项目名称")
    
    # 回款金额字段
    estimated_possible_at_start = Column(
        Numeric(15, 2), default=0.00, comment="月初预计可能回款"
    )
    estimated_confirmed_at_start = Column(
        Numeric(15, 2), default=0.00, comment="月初预计确定回款"
    )
    possible_collection = Column(
        Numeric(15, 2), default=0.00, comment="可能回款"
    )
    confirmed_collection = Column(
        Numeric(15, 2), default=0.00, comment="确定回款"
    )
    actual_collection = Column(
        Numeric(15, 2), default=0.00, comment="实际回款"
    )
    uncollected_amount = Column(
        Numeric(15, 2), default=0.00, comment="未回款金额"
    )
    
    # 备注字段
    reason_for_non_completion = Column(
        Text, nullable=True, comment="未完成原因"
    )
    solution = Column(Text, nullable=True, comment="解决办法")
    
    # 元数据
    month = Column(String(20), nullable=False, comment="月份，格式：YYYY-MM")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    
    # 用于标识是否为小计行
    is_subtotal = Column(Integer, default=0, comment="是否为小计行：0-否，1-是")


class ContractRecord(Base):
    """合同记录表"""
    __tablename__ = "contract_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # 基本信息
    responsible_person = Column(String(100), nullable=False, comment="负责人")
    company_name = Column(String(200), nullable=True, comment="公司名称")
    project_name = Column(String(200), nullable=False, comment="项目名称")
    
    # 合同金额字段
    estimated_possible_at_start = Column(
        Numeric(15, 2), default=0.00, comment="月初预计可能合同"
    )
    estimated_confirmed_at_start = Column(
        Numeric(15, 2), default=0.00, comment="月初预计确定合同"
    )
    possible_contract = Column(
        Numeric(15, 2), default=0.00, comment="可能合同"
    )
    confirmed_contract = Column(
        Numeric(15, 2), default=0.00, comment="确定合同"
    )
    actual_contract = Column(
        Numeric(15, 2), default=0.00, comment="实际合同"
    )
    
    # 备注字段
    completion_status = Column(Text, nullable=True, comment="完成情况")
    
    # 元数据
    month = Column(String(20), nullable=False, comment="月份，格式：YYYY-MM")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    
    # 用于标识是否为小计行
    is_subtotal = Column(Integer, default=0, comment="是否为小计行：0-否，1-是")


def get_engine(db_path: str = "data/financial_data.db"):
    """获取数据库引擎"""
    import os
    from pathlib import Path
    
    # 确保目录存在
    db_dir = Path(db_path).parent
    db_dir.mkdir(parents=True, exist_ok=True)
    
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    return engine


def init_database(db_path: str = "data/financial_data.db"):
    """初始化数据库，创建所有表"""
    engine = get_engine(db_path)
    Base.metadata.create_all(engine)
    return engine


def get_session(db_path: str = "data/financial_data.db"):
    """获取数据库会话"""
    engine = get_engine(db_path)
    Session = sessionmaker(bind=engine)
    return Session()
