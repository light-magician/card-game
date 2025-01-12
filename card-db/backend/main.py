from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import numpy as np
from pgvector.sqlalchemy import Vector

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
SQLALCHEMY_DATABASE_URL = "postgresql://yugiohadmin:yugiohpass@db:5432/yugiohdb"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Models
class Card(Base):
    __tablename__ = "cards"
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    type_field = Column(String)
    frame_type = Column(String)
    desc = Column(String)
    desc_embedding = Column(Vector(384))  # BERT embedding dimension
    race = Column(String)
    archetype = Column(String, nullable=True)
    atk = Column(Integer, nullable=True)
    def_ = Column(Integer, nullable=True)
    level = Column(Integer, nullable=True)
    attribute = Column(String, nullable=True)
    pend_desc = Column(String, nullable=True)
    monster_desc = Column(String, nullable=True)
    scale = Column(Integer, nullable=True)
    linkval = Column(Integer, nullable=True)
    linkmarkers = Column(JSON, nullable=True)
    
    card_sets = relationship("CardSet", back_populates="card")
    card_images = relationship("CardImage", back_populates="card")
    card_prices = relationship("CardPrice", back_populates="card")
    banlist_info = relationship("BanlistInfo", back_populates="card", uselist=False)

class CardSet(Base):
    __tablename__ = "card_sets"
    
    id = Column(Integer, primary_key=True)
    card_id = Column(Integer, ForeignKey("cards.id"))
    set_name = Column(String)
    set_code = Column(String)
    set_rarity = Column(String)
    set_rarity_code = Column(String)
    set_price = Column(String)
    
    card = relationship("Card", back_populates="card_sets")

class CardImage(Base):
    __tablename__ = "card_images"
    
    id = Column(Integer, primary_key=True)
    card_id = Column(Integer, ForeignKey("cards.id"))
    image_url = Column(String)
    image_url_small = Column(String)
    image_url_cropped = Column(String)
    
    card = relationship("Card", back_populates="card_images")

class CardPrice(Base):
    __tablename__ = "card_prices"
    
    id = Column(Integer, primary_key=True)
    card_id = Column(Integer, ForeignKey("cards.id"))
    cardmarket_price = Column(String)
    tcgplayer_price = Column(String)
    ebay_price = Column(String)
    amazon_price = Column(String)
    coolstuffinc_price = Column(String)
    
    card = relationship("Card", back_populates="card_prices")

class BanlistInfo(Base):
    __tablename__ = "banlist_info"
    
    id = Column(Integer, primary_key=True)
    card_id = Column(Integer, ForeignKey("cards.id"))
    ban_tcg = Column(String, nullable=True)
    ban_ocg = Column(String, nullable=True)
    ban_goat = Column(String, nullable=True)
    
    card = relationship("Card", back_populates="banlist_info")

# Initialize sentence transformer
model = SentenceTransformer('all-MiniLM-L6-v2')

# Pydantic models for request/response
class CardBase(BaseModel):
    id: int
    name: str
    type_field: str
    frame_type: str
    desc: str
    race: str
    archetype: str | None = None
    atk: int | None = None
    def_: int | None = None
    level: int | None = None
    attribute: str | None = None
    pend_desc: str | None = None
    monster_desc: str | None = None
    scale: int | None = None
    linkval: int | None = None
    linkmarkers: list[str] | None = None

@app.post("/cards/")
async def create_cards(cards: list[CardBase]):
    db = SessionLocal()
    try:
        for card_data in cards:
            # Generate embedding for card description
            embedding = model.encode(card_data.desc)
            
            card = Card(
                id=card_data.id,
                name=card_data.name,
                type_field=card_data.type_field,
                frame_type=card_data.frame_type,
                desc=card_data.desc,
                desc_embedding=embedding.tolist(),
                race=card_data.race,
                archetype=card_data.archetype,
                atk=card_data.atk,
                def_=card_data.def_,
                level=card_data.level,
                attribute=card_data.attribute,
                pend_desc=card_data.pend_desc,
                monster_desc=card_data.monster_desc,
                scale=card_data.scale,
                linkval=card_data.linkval,
                linkmarkers=card_data.linkmarkers
            )
            db.add(card)
        db.commit()
        return {"message": "Cards created successfully"}
    finally:
        db.close()

@app.get("/cards/search")
async def search_cards(query: str, limit: int = 10):
    db = SessionLocal()
    try:
        # Generate embedding for search query
        query_embedding = model.encode(query)
        
        # Perform similarity search using pgvector
        results = db.query(Card).order_by(
            Card.desc_embedding.cosine_distance(query_embedding)
        ).limit(limit).all()
        
        return results
    finally:
        db.close()

@app.get("/cards/{card_id}")
async def get_card(card_id: int):
    db = SessionLocal()
    try:
        card = db.query(Card).filter(Card.id == card_id).first()
        if card is None:
            raise HTTPException(status_code=404, detail="Card not found")
        return card
    finally:
        db.close()

# Create tables
Base.metadata.create_all(bind=engine)
