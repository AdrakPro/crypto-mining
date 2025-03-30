from sqlalchemy.orm import Session
from datetime import datetime
from .database import Client

def get_client_by_ip(db: Session, ip_address: str):
    """Get client by IP address"""
    return db.query(Client).filter(Client.ip_address == ip_address).first()

def get_client_by_username(db: Session, username: str):
    """Get client by username"""
    return db.query(Client).filter(Client.username == username).first()

def create_client(db: Session, ip_address: str, username: str, password: str):
    """Create a new client record"""
    db_client = Client(
        username=username,
        password=password,
        ip_address=ip_address,
        last_seen=datetime.utcnow(),
        tasks_completed=0,
        success_rate=0.0
    )
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client

def update_client_ping(db: Session, ip_address: str,  username: str, password: str):
    """Update client last seen timestamp"""
    client = get_client_by_ip(db, ip_address)
    if client:
        client.last_seen = datetime.utcnow()
        db.commit()
        db.refresh(client)
        return client
    return create_client(db, ip_address, username, password)

def update_client_task_completion(db: Session, ip_address: str, is_correct: bool,  username: str, password: str):
    """Update client task statistics"""
    client = get_client_by_ip(db, ip_address)
    if not client:
        client = create_client(db, ip_address, username, password)
    
    client.tasks_completed += 1
    
    # Update success rate
    if is_correct:
        # Calculate new success rate based on previous successes and total tasks
        current_successes = client.success_rate * (client.tasks_completed - 1)
        new_successes = current_successes + 1
        client.success_rate = new_successes / client.tasks_completed
    else:
        # Recalculate success rate
        current_successes = client.success_rate * (client.tasks_completed - 1)
        client.success_rate = current_successes / client.tasks_completed
    
    db.commit()
    db.refresh(client)
    return client