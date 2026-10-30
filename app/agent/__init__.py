"""The support agent behind the Help chat.

Which model answers is a backend setting in `agent.env`, read on every
message. Every provider gets the same prompt and the same tools, and every
failure becomes an honest handoff to the business.
"""
