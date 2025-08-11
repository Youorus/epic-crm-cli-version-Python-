# services/crud/base.py
from typing import Generic, TypeVar, Optional, Callable, Iterable
from sqlalchemy.orm import Session

TOrm = TypeVar("TOrm")
TEnt = TypeVar("TEnt")

class OrmRepository(Generic[TOrm, TEnt]):
    """
    Base générique. Les classes concrètes doivent fournir:
      - orm_cls: type ORM (table)
      - to_entity(orm) -> entité domaine
      - apply_entity(orm, entité) -> None
      - new_orm_from_entity(entité) -> ORM
    """
    orm_cls: type[TOrm]
    to_entity: Callable[[TOrm], TEnt]
    new_orm_from_entity: Callable[[TEnt], TOrm]
    apply_entity: Callable[[TOrm, TEnt], None]

    def __init__(self, session: Session):
        self.s = session

    def get(self, id_: int) -> Optional[TEnt]:
        orm = self.s.get(self.orm_cls, id_)
        return self.to_entity(orm) if orm else None

    def list(self) -> Iterable[TEnt]:
        for orm in self.s.query(self.orm_cls).all():
            yield self.to_entity(orm)

    def add(self, ent: TEnt) -> TEnt:
        orm = self.new_orm_from_entity(ent)
        self.s.add(orm)
        self.s.flush()  # PK disponible
        return self.to_entity(orm)

    def update(self, ent: TEnt) -> TEnt:
        if getattr(ent, "id", None) is None:
            raise ValueError("update() requiert une entité avec id.")
        orm = self.s.get(self.orm_cls, ent.id)
        if not orm:
            raise ValueError("Entité introuvable.")
        self.apply_entity(orm, ent)
        self.s.flush()
        try:
            self.s.refresh(orm)
        except Exception:
            pass
        return self.to_entity(orm)

    def delete(self, id_: int) -> None:
        orm = self.s.get(self.orm_cls, id_)
        if orm:
            self.s.delete(orm)