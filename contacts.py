#!/usr/bin/env python3
"""
Telegram Contact-Lister + CSV + vCard exporter
Interactive account chooser on every run.
"""

import os
import csv
import asyncio
from pathlib import Path

import yaml
from rich.console import Console
from rich.prompt import Prompt, IntPrompt, Confirm
from pyrogram import Client
from colorama import just_fix_windows_console
just_fix_windows_console()

CONFIG_FILE = Path("config.yml")
CSV_FILE    = Path("contacts.csv")
VCARD_FILE  = Path("contacts.vcf")

console = Console()

# --------------------------------------------------------------------------- #
# 1. Config helpers
# --------------------------------------------------------------------------- #
def load_config() -> dict:
    if CONFIG_FILE.exists():
        with CONFIG_FILE.open("rt", encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}
    return {}


def save_config(cfg: dict) -> None:
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with CONFIG_FILE.open("wt", encoding="utf-8") as fh:
        yaml.dump(cfg, fh, default_flow_style=False, sort_keys=True)
    console.print(f"[dim]Saved {CONFIG_FILE.absolute()}[/dim]")


async def interactive_login(cfg: dict) -> None:
    """Update cfg with new session_string (phone login)."""
    api_id = cfg.get("api_id") or IntPrompt.ask("[cyan]API_ID[/cyan]")
    api_hash = cfg.get("api_hash") or Prompt.ask("[cyan]API_HASH[/cyan]").strip()

    client = Client(
        name="temp_session",
        api_id=api_id,
        api_hash=api_hash,
        workdir=".",
        no_updates=True,
    )

    async with client:
        session_string = await client.export_session_string()
        cfg.update(api_id=api_id, api_hash=api_hash, session_string=session_string)
        save_config(cfg)


# --------------------------------------------------------------------------- #
# 2. CSV & vCard writers
# --------------------------------------------------------------------------- #
def write_csv(contacts) -> None:
    with CSV_FILE.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["user_id", "first_name", "last_name", "username", "phone"])
        for u in contacts:
            writer.writerow([
                u.id,
                u.first_name or "",
                u.last_name or "",
                u.username or "",
                u.phone_number or ""
            ])
    console.print(f"[green]CSV saved → {CSV_FILE.resolve()}[/green]")


def write_vcard(contacts) -> None:
    with VCARD_FILE.open("w", encoding="utf-8") as fh:
        for u in contacts:
            name = " ".join(filter(None, [u.first_name, u.last_name]))
            phone = u.phone_number or ""
            if not phone:
                continue
            fh.write("BEGIN:VCARD\n")
            fh.write("VERSION:3.0\n")
            fh.write(f"FN:{name}\n")
            fh.write(f"TEL;TYPE=CELL:{phone}\n")
            if u.username:
                fh.write(f"NOTE:https://t.me/{u.username}\n")
            fh.write("END:VCARD\n")
    console.print(f"[green]vCard saved → {VCARD_FILE.resolve()}[/green]")


# --------------------------------------------------------------------------- #
# 3. Main
# --------------------------------------------------------------------------- #
async def main() -> None:
    cfg = load_config()

    # Ensure we have API credentials
    if not cfg.get("api_id") or not cfg.get("api_hash"):
        console.print("[yellow]Missing API credentials – starting interactive login[/yellow]")
        await interactive_login(cfg)

    # Always open a lightweight client just to show who we are
    client = Client(
        name="temp_session",
        api_id=cfg["api_id"],
        api_hash=cfg["api_hash"],
        session_string=cfg.get("session_string"),
        no_updates=True,
    )

    async with client:
        me = await client.get_me()
        console.print(
            f"\n[bold green]Current session belongs to:[/bold green] "
            f"{me.first_name} (@{me.username or 'no-username'})\n"
        )

        if not Confirm.ask("Proceed with this account?"):
            # User wants another number → reset
            console.print("[yellow]Switching account…[/yellow]")
            CSV_FILE.unlink(missing_ok=True)
            VCARD_FILE.unlink(missing_ok=True)
            cfg.pop("session_string", None)
            save_config(cfg)
            console.print("[cyan]Please log in with the new phone number.[/cyan]")
            await interactive_login(cfg)
            # Recursive call to restart the whole routine
            return await main()

        # ------------------ Normal flow ------------------ #
        contacts = await client.get_contacts()
        console.print(f"[bold blue]Total contacts retrieved:[/bold blue] {len(contacts)}\n")

        # Screen preview
        for u in sorted(contacts, key=lambda c: (c.first_name or "").lower()):
            console.print(
                f"[magenta]{u.id:>12}[/magenta] "
                f"[white]{u.first_name or ''} {u.last_name or ''}[/white] "
                f"[dim]@{u.username or ''}[/dim] "
                f"[cyan]{u.phone_number or ''}[/cyan]"
            )

        write_csv(contacts)
        write_vcard(contacts)
        console.print(f"\n[bold green]✅ Done! {len(contacts)} contacts exported.[/bold green]")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[red]Aborted by user[/red]")