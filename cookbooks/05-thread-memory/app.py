"""Recipe 05 — Thread memory: short-term chat history in one session."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ThreadMemory:
    messages: list[dict[str, str]] = field(default_factory=list)
    max_turns: int = 8

    def add(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})
        overflow = len(self.messages) - self.max_turns * 2
        if overflow > 0:
            self.messages = self.messages[overflow:]

    def as_prompt(self) -> list[dict[str, str]]:
        return list(self.messages)


def reply_with_memory(memory: ThreadMemory, user_text: str) -> str:
    memory.add("user", user_text)
    last_user = [m["content"] for m in memory.messages if m["role"] == "user"]
    if len(last_user) == 1:
        reply = f"Acknowledged first message: {user_text}"
    else:
        reply = f"I remember {len(last_user)} user turns. Latest: {user_text}"
    memory.add("assistant", reply)
    return reply


if __name__ == "__main__":
    mem = ThreadMemory()
    print(reply_with_memory(mem, "My name is Jared."))
    print(reply_with_memory(mem, "What is my name?"))
