"""
Document Skill
==============

Read, write, search, and summarise documents from the local filesystem or
cloud storage providers (Google Drive, SharePoint/OneDrive).

- **read**       – Read a file or remote document
- **write**      – Write/append content to a file
- **search**     – Full-text search across a directory or Drive folder
- **list**       – List files in a directory or Drive folder
- **delete**     – Delete a file (with a safety confirmation flag)
- **summarise**  – Extract a plain-text summary of a document

Configuration keys (``api_config``)::

    {
        "provider":         "local" | "gdrive" | "sharepoint",
        "gdrive_token":     "ya29...",
        "sharepoint_token": "eyJ...",
        "sharepoint_site":  "https://contoso.sharepoint.com/sites/mysite",
        "base_path":        "/home/agent/workspace"   # local root
    }
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from achilles.modules.skills import Skill

logger = logging.getLogger(__name__)


class DocumentSkill(Skill):
    """Document management skill (read, write, search, summarise)."""

    name: str = "document"
    description: str = (
        "Read, write, search, and summarise documents on the local filesystem "
        "or in cloud storage (Google Drive, SharePoint)."
    )

    def _build_action_map(self) -> Dict[str, Callable]:
        return {
            "read": self._read,
            "write": self._write,
            "search": self._search,
            "list": self._list,
            "delete": self._delete,
            "summarise": self._summarise,
        }

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    async def _read(
        self,
        path: str,
        encoding: str = "utf-8",
    ) -> Dict[str, Any]:
        """
        Read a document.

        Args:
            path:     File path (local) or Drive/SharePoint file ID / URL.
            encoding: Text encoding for local files (default ``"utf-8"``).

        Returns:
            Dict with ``content`` (str) and file metadata.
        """
        provider = self.api_config.get("provider", "local")
        if provider == "gdrive":
            return await self._gdrive_read(path)
        elif provider == "sharepoint":
            return await self._sp_read(path)
        else:
            return self._local_read(path, encoding)

    async def _write(
        self,
        path: str,
        content: str,
        mode: str = "write",
        encoding: str = "utf-8",
        create_dirs: bool = True,
    ) -> Dict[str, Any]:
        """
        Write content to a document.

        Args:
            path:        Target file path or Drive/SharePoint destination.
            content:     String content to write.
            mode:        ``"write"`` (overwrite) or ``"append"``.
            encoding:    Text encoding for local files.
            create_dirs: If True, create missing parent directories.

        Returns:
            Write receipt.
        """
        provider = self.api_config.get("provider", "local")
        if provider == "gdrive":
            return await self._gdrive_write(path, content)
        elif provider == "sharepoint":
            return await self._sp_write(path, content)
        else:
            return self._local_write(path, content, mode, encoding, create_dirs)

    async def _search(
        self,
        query: str,
        location: Optional[str] = None,
        file_types: Optional[List[str]] = None,
        max_results: int = 20,
    ) -> Dict[str, Any]:
        """
        Full-text search for documents.

        Args:
            query:       Search string.
            location:    Directory (local) or folder ID (Drive/SharePoint).
            file_types:  Filter by extensions, e.g. ``[".txt", ".md"]``.
            max_results: Cap on number of results.

        Returns:
            Dict with ``results`` list and ``count``.
        """
        provider = self.api_config.get("provider", "local")
        if provider == "gdrive":
            return await self._gdrive_search(query, location, max_results)
        elif provider == "sharepoint":
            return await self._sp_search(query, location, max_results)
        else:
            return self._local_search(query, location, file_types, max_results)

    async def _list(
        self,
        location: Optional[str] = None,
        recursive: bool = False,
        file_types: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        List files in a directory or folder.

        Args:
            location:   Directory path or Drive/SharePoint folder ID.
            recursive:  Include subdirectories.
            file_types: Filter by extension list.

        Returns:
            Dict with ``files`` list.
        """
        provider = self.api_config.get("provider", "local")
        if provider == "gdrive":
            return await self._gdrive_list(location)
        elif provider == "sharepoint":
            return await self._sp_list(location)
        else:
            return self._local_list(location, recursive, file_types)

    async def _delete(
        self,
        path: str,
        confirmed: bool = False,
    ) -> Dict[str, Any]:
        """
        Delete a file.

        Args:
            path:      File path or Drive/SharePoint ID.
            confirmed: Must be ``True`` to proceed (safety gate).

        Returns:
            Deletion receipt.
        """
        if not confirmed:
            return {
                "skill": "document",
                "action": "delete",
                "status": "requires_confirmation",
                "message": "Set confirmed=True to permanently delete the file.",
                "path": path,
            }
        provider = self.api_config.get("provider", "local")
        if provider == "gdrive":
            return await self._gdrive_delete(path)
        elif provider == "sharepoint":
            return await self._sp_delete(path)
        else:
            return self._local_delete(path)

    async def _summarise(
        self,
        path: Optional[str] = None,
        content: Optional[str] = None,
        max_sentences: int = 5,
    ) -> Dict[str, Any]:
        """
        Extract a plain-text summary.

        Either *path* or *content* must be provided.  The summariser uses a
        simple frequency-based extractive approach; when an AI provider is
        available more advanced summarisation can be piped in.

        Args:
            path:          Path to document (will be read automatically).
            content:       Pre-loaded document text.
            max_sentences: Maximum sentences in the summary.

        Returns:
            Dict with ``summary`` string.
        """
        if path and not content:
            read_result = await self._read(path)
            content = read_result.get("content", "")

        if not content:
            return {"skill": "document", "action": "summarise", "summary": "",
                    "status": "no_content"}

        summary = self._extractive_summary(content, max_sentences)
        return {
            "skill": "document",
            "action": "summarise",
            "summary": summary,
            "characters_read": len(content),
            "sentences_in_summary": max_sentences,
        }

    # ------------------------------------------------------------------
    # Local filesystem
    # ------------------------------------------------------------------

    def _resolve_path(self, path: str) -> Path:
        base = self.api_config.get("base_path", "")
        p = Path(path)
        if base and not p.is_absolute():
            p = Path(base) / p
        return p

    def _local_read(self, path: str, encoding: str) -> Dict[str, Any]:
        p = self._resolve_path(path)
        try:
            content = p.read_text(encoding=encoding)
            stat = p.stat()
            return {
                "skill": "document",
                "action": "read",
                "path": str(p),
                "content": content,
                "size_bytes": stat.st_size,
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            }
        except Exception as exc:
            logger.error("Document read failed: %s", exc)
            return {"skill": "document", "action": "read", "status": "error",
                    "reason": str(exc), "path": path}

    def _local_write(
        self, path: str, content: str, mode: str, encoding: str, create_dirs: bool
    ) -> Dict[str, Any]:
        p = self._resolve_path(path)
        try:
            if create_dirs:
                p.parent.mkdir(parents=True, exist_ok=True)
            if mode == "append" and p.exists():
                existing = p.read_text(encoding=encoding)
                final_content = existing + content
            else:
                final_content = content
            p.write_text(final_content, encoding=encoding)
            return {"skill": "document", "action": "write", "status": "written",
                    "path": str(p), "bytes_written": len(content.encode(encoding))}
        except Exception as exc:
            logger.error("Document write failed: %s", exc)
            return {"skill": "document", "action": "write", "status": "error",
                    "reason": str(exc)}

    def _local_search(
        self,
        query: str,
        location: Optional[str],
        file_types: Optional[List[str]],
        max_results: int,
    ) -> Dict[str, Any]:
        root = self._resolve_path(location or ".")
        results: List[Dict[str, Any]] = []
        try:
            for p in root.rglob("*"):
                if not p.is_file():
                    continue
                if file_types and p.suffix not in file_types:
                    continue
                try:
                    text = p.read_text(errors="ignore")
                    if query.lower() in text.lower():
                        idx = text.lower().find(query.lower())
                        snippet = text[max(0, idx - 50): idx + 100].replace("\n", " ")
                        results.append({"path": str(p), "snippet": snippet})
                        if len(results) >= max_results:
                            break
                except Exception:
                    continue
        except Exception as exc:
            return {"skill": "document", "action": "search", "status": "error",
                    "reason": str(exc)}
        return {"skill": "document", "action": "search",
                "results": results, "count": len(results)}

    def _local_list(
        self,
        location: Optional[str],
        recursive: bool,
        file_types: Optional[List[str]],
    ) -> Dict[str, Any]:
        root = self._resolve_path(location or ".")
        try:
            iterator = root.rglob("*") if recursive else root.iterdir()
            files = []
            for p in iterator:
                if p.is_file():
                    if file_types and p.suffix not in file_types:
                        continue
                    files.append({"path": str(p), "size_bytes": p.stat().st_size,
                                  "modified_at": datetime.fromtimestamp(p.stat().st_mtime).isoformat()})
            return {"skill": "document", "action": "list", "files": files,
                    "count": len(files)}
        except Exception as exc:
            return {"skill": "document", "action": "list", "status": "error",
                    "reason": str(exc)}

    def _local_delete(self, path: str) -> Dict[str, Any]:
        p = self._resolve_path(path)
        try:
            p.unlink()
            return {"skill": "document", "action": "delete", "status": "deleted",
                    "path": str(p)}
        except Exception as exc:
            return {"skill": "document", "action": "delete", "status": "error",
                    "reason": str(exc)}

    # ------------------------------------------------------------------
    # Google Drive API stubs
    # ------------------------------------------------------------------

    async def _gdrive_read(self, file_id: str) -> Dict[str, Any]:
        try:
            import aiohttp
        except ImportError:
            return {"skill": "document", "action": "read", "status": "error",
                    "reason": "aiohttp not installed"}

        import aiohttp

        token = self.api_config.get("gdrive_token", "")
        url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"
        async with aiohttp.ClientSession() as s:
            async with s.get(url, headers={"Authorization": f"Bearer {token}"}) as resp:
                content = await resp.text()
                return {"skill": "document", "action": "read", "file_id": file_id,
                        "content": content}

    async def _gdrive_write(self, name: str, content: str) -> Dict[str, Any]:
        try:
            import aiohttp
        except ImportError:
            return {"skill": "document", "action": "write", "status": "error"}

        token = self.api_config.get("gdrive_token", "")
        metadata = json.dumps({"name": name, "mimeType": "text/plain"})
        data = aiohttp.FormData()
        data.add_field("metadata", metadata, content_type="application/json")
        data.add_field("file", content, content_type="text/plain")
        async with aiohttp.ClientSession() as s:
            async with s.post(
                "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart",
                headers={"Authorization": f"Bearer {token}"},
                data=data,
            ) as resp:
                result = await resp.json()
                return {"skill": "document", "action": "write", "status": "written",
                        "file": result}

    async def _gdrive_search(
        self, query: str, folder_id: Optional[str], max_results: int
    ) -> Dict[str, Any]:
        try:
            import aiohttp
        except ImportError:
            return {"skill": "document", "action": "search", "results": [], "count": 0}

        token = self.api_config.get("gdrive_token", "")
        q = f"fullText contains '{query}'"
        if folder_id:
            q += f" and '{folder_id}' in parents"
        url = (
            "https://www.googleapis.com/drive/v3/files"
            f"?q={q}&pageSize={max_results}&fields=files(id,name,mimeType)"
        )
        async with aiohttp.ClientSession() as s:
            async with s.get(url, headers={"Authorization": f"Bearer {token}"}) as resp:
                data = await resp.json()
                items = data.get("files", [])
                return {"skill": "document", "action": "search",
                        "results": items, "count": len(items)}

    async def _gdrive_list(self, folder_id: Optional[str]) -> Dict[str, Any]:
        try:
            import aiohttp
        except ImportError:
            return {"skill": "document", "action": "list", "files": [], "count": 0}

        token = self.api_config.get("gdrive_token", "")
        q = f"'{folder_id or 'root'}' in parents and trashed=false"
        url = (
            "https://www.googleapis.com/drive/v3/files"
            f"?q={q}&fields=files(id,name,mimeType,size,modifiedTime)"
        )
        async with aiohttp.ClientSession() as s:
            async with s.get(url, headers={"Authorization": f"Bearer {token}"}) as resp:
                data = await resp.json()
                files = data.get("files", [])
                return {"skill": "document", "action": "list",
                        "files": files, "count": len(files)}

    async def _gdrive_delete(self, file_id: str) -> Dict[str, Any]:
        try:
            import aiohttp
        except ImportError:
            return {"skill": "document", "action": "delete", "status": "error"}

        token = self.api_config.get("gdrive_token", "")
        url = f"https://www.googleapis.com/drive/v3/files/{file_id}"
        async with aiohttp.ClientSession() as s:
            async with s.delete(url, headers={"Authorization": f"Bearer {token}"}) as resp:
                ok = resp.status == 204
                return {"skill": "document", "action": "delete",
                        "status": "deleted" if ok else "error", "file_id": file_id}

    # ------------------------------------------------------------------
    # SharePoint / Microsoft Graph stubs
    # ------------------------------------------------------------------

    async def _sp_read(self, item_id: str) -> Dict[str, Any]:
        try:
            import aiohttp
        except ImportError:
            return {"skill": "document", "action": "read", "status": "error"}

        token = self.api_config.get("sharepoint_token", "")
        site = self.api_config.get("sharepoint_site", "")
        url = f"{site}/_api/v2.0/drive/items/{item_id}/content"
        async with aiohttp.ClientSession() as s:
            async with s.get(url, headers={"Authorization": f"Bearer {token}"}) as resp:
                content = await resp.text()
                return {"skill": "document", "action": "read",
                        "item_id": item_id, "content": content}

    async def _sp_write(self, path: str, content: str) -> Dict[str, Any]:
        try:
            import aiohttp
        except ImportError:
            return {"skill": "document", "action": "write", "status": "error"}

        token = self.api_config.get("sharepoint_token", "")
        site = self.api_config.get("sharepoint_site", "")
        url = f"{site}/_api/v2.0/drive/root:/{path}:/content"
        async with aiohttp.ClientSession() as s:
            async with s.put(
                url,
                headers={"Authorization": f"Bearer {token}",
                         "Content-Type": "text/plain"},
                data=content.encode("utf-8"),
            ) as resp:
                data = await resp.json()
                return {"skill": "document", "action": "write", "status": "written",
                        "item": data}

    async def _sp_search(
        self, query: str, location: Optional[str], max_results: int
    ) -> Dict[str, Any]:
        try:
            import aiohttp
        except ImportError:
            return {"skill": "document", "action": "search", "results": [], "count": 0}

        token = self.api_config.get("sharepoint_token", "")
        url = (
            "https://graph.microsoft.com/v1.0/search/query"
        )
        payload = {
            "requests": [{
                "entityTypes": ["driveItem"],
                "query": {"queryString": query},
                "size": max_results,
            }]
        }
        async with aiohttp.ClientSession() as s:
            async with s.post(url, headers={"Authorization": f"Bearer {token}"},
                              json=payload) as resp:
                data = await resp.json()
                return {"skill": "document", "action": "search",
                        "results": data.get("value", []), "count": 0}

    async def _sp_list(self, folder_path: Optional[str]) -> Dict[str, Any]:
        try:
            import aiohttp
        except ImportError:
            return {"skill": "document", "action": "list", "files": [], "count": 0}

        token = self.api_config.get("sharepoint_token", "")
        site = self.api_config.get("sharepoint_site", "")
        path_part = f":/{folder_path}:" if folder_path else ""
        url = f"{site}/_api/v2.0/drive/root{path_part}/children"
        async with aiohttp.ClientSession() as s:
            async with s.get(url, headers={"Authorization": f"Bearer {token}"}) as resp:
                data = await resp.json()
                files = data.get("value", [])
                return {"skill": "document", "action": "list",
                        "files": files, "count": len(files)}

    async def _sp_delete(self, item_id: str) -> Dict[str, Any]:
        try:
            import aiohttp
        except ImportError:
            return {"skill": "document", "action": "delete", "status": "error"}

        token = self.api_config.get("sharepoint_token", "")
        site = self.api_config.get("sharepoint_site", "")
        url = f"{site}/_api/v2.0/drive/items/{item_id}"
        async with aiohttp.ClientSession() as s:
            async with s.delete(url, headers={"Authorization": f"Bearer {token}"}) as resp:
                ok = resp.status == 204
                return {"skill": "document", "action": "delete",
                        "status": "deleted" if ok else "error", "item_id": item_id}

    # ------------------------------------------------------------------
    # Extractive summariser
    # ------------------------------------------------------------------

    @staticmethod
    def _extractive_summary(text: str, max_sentences: int) -> str:
        """Simple frequency-based extractive summary."""
        import re
        from collections import Counter

        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
        if not sentences:
            return text[:500]
        if len(sentences) <= max_sentences:
            return " ".join(sentences)

        # Word frequency
        words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
        freq = Counter(words)

        # Score sentences
        def score(sentence: str) -> float:
            ws = re.findall(r"\b[a-zA-Z]{3,}\b", sentence.lower())
            return sum(freq[w] for w in ws) / max(len(ws), 1)

        ranked = sorted(range(len(sentences)), key=lambda i: score(sentences[i]), reverse=True)
        top = sorted(ranked[:max_sentences])
        return " ".join(sentences[i] for i in top)


__all__ = ["DocumentSkill"]
