import asyncio
import aiosqlite
import os
from typing import Optional, List

from jupyter_core.paths import jupyter_data_dir
from .models import ListTasksResponse, ListTasksEntry, DescribeTaskResponse, ListEnginesEntry

class TaskManager:
    db_path = os.path.join(jupyter_data_dir(), "ai_task_manager.db")

    def __init__(self, engines, default_tasks):
        self.engines = engines
        self.default_tasks = default_tasks
        self.db_initialized = asyncio.create_task(self.init_db())
 
    async def init_db(self):
        async with aiosqlite.connect(self.db_path) as con:
            await con.execute(
                "CREATE TABLE IF NOT EXISTS tasks ("
                "id TEXT NOT NULL PRIMARY KEY, "
                "name TEXT NOT NULL, "
                "prompt_template TEXT NOT NULL, "
                "modality TEXT NOT NULL, "
                "insertion_mode TEXT NOT NULL, "
                "is_default INTEGER NOT NULL"
                ")"
            )

            # delete and recreate all default tasks. this ensures the default
            # tasks are all up-to-date.
            await con.execute("DELETE FROM tasks WHERE is_default = 1")
            for task in self.default_tasks:
                await con.execute(
                    "INSERT INTO tasks (id, name, prompt_template, modality, insertion_mode, is_default) VALUES (?, ?, ?, ?, ?, ?)",
                    (task["id"], task["name"], task["prompt_template"], task["modality"], task["insertion_mode"], 1)
                )
            
            await con.commit()
    
    async def list_tasks(self) -> ListTasksResponse:
        await self.db_initialized
        async with aiosqlite.connect(self.db_path) as con:
            cursor = await con.execute(
                "SELECT id, name FROM tasks"
            )
            rows = await cursor.fetchall()
            tasks = []

            if not rows:
                return tasks
            
            for row in rows:
                tasks.append(ListTasksEntry(
                    id=row[0],
                    name=row[1]
                ))
            
            return ListTasksResponse(tasks=tasks)
        
    async def describe_task(self, id: str) -> Optional[DescribeTaskResponse]:
        await self.db_initialized
        async with aiosqlite.connect(self.db_path) as con:
            cursor = await con.execute(
                "SELECT name, prompt_template, modality, insertion_mode FROM tasks WHERE id = ?", (id,)
            )
            row = await cursor.fetchone()

            if row is None:
                return None

            # determine what engines are available for the task's modality
            engines: List[ListEnginesEntry] = []
            modality = row[2]
            for engine in self.engines.values():
                if modality in engine.modalities:
                    engines.append(ListEnginesEntry(id=engine.id, name=engine.name))
            
            # sort engines A-Z
            engines = sorted(engines, key=lambda engine: engine.name)
            
            return DescribeTaskResponse(
                name=row[0],
                prompt_template=row[1],
                modality=row[2],
                insertion_mode=row[3],
                engines=engines
            )
    