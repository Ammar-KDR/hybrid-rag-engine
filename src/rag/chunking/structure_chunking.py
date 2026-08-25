from rag.ingestion.model import Document, Chunk
import re


class MarkdownStructureChunker:
    def __init__(self,max_chunk_chars: int = 2000,overlap: int = 200):
        if max_chunk_chars <= 0:
            raise ValueError("chunk_size must be a positive integer")
        elif overlap < 0 or overlap >= max_chunk_chars:
            raise ValueError("overlap must be a non-negative integer less than chunk_size")
        self.max_chunk_chars = max_chunk_chars
        self.overlap = overlap


    def extract_sections(self,document:Document) ->list:
            pattern= r"^(#{1,6})\s+(.+)$"
            sections = []
            text=document.text
            matches = list(re.finditer(pattern, text, re.MULTILINE))
            if not matches:
                cleaned_text = text.strip()

                if not cleaned_text:
                    return []

                return [
                    {
                        "heading": None,
                        "heading_level": None,
                        "heading_path": [],
                        "text": cleaned_text,
                    }
                ]
            if matches and matches[0].start() > 0:
                intro_text = text[:matches[0].start()].strip()

                if intro_text:
                    sections.append({
                        "heading": None,
                        "heading_level": None,
                        "heading_path": [],
                        "text": intro_text,
                    })
            current_path=[]
            last_level=0
            
            for i, match in enumerate(matches):
                level_symbols = match.group(1)
                heading_text = match.group(2)
                level_number = len(level_symbols)
                

    # Adjust path based on heading level
                if level_number > last_level:
                    current_path.append(heading_text)
                elif level_number <= last_level:
                    # Pop elements from path until the level matches or is above
                    while len(current_path) >= level_number:
                        current_path.pop()
                    current_path.append(heading_text)
                last_level=level_number

                # Content ends at the start of the next heading or the end of the text
                content_end = len(text)
                if i + 1 < len(matches):
                    content_end = matches[i + 1].start()

                # Extract content and strip leading/trailing whitespace
                content = text[match.end():content_end].strip()

                if not content:
                    continue

                sections.append({
                    'heading': heading_text,
                    'heading_level': level_number,
                    'heading_path':current_path.copy(),
                    'text': content
                })
            return sections

    def chunk(self,document:Document)-> list[Chunk]:
        sections=self.extract_sections(document)
        chunks=[]
        chunk_ind=0
        for section in sections:
            if len(section["text"])>self.max_chunk_chars:
                step_size= self.max_chunk_chars - self.overlap
                section_number=0
                for i in range(0,len(section["text"]),step_size):
                    text=section["text"]
                    start_ind=i
                    end_ind = min(i + self.max_chunk_chars, len(text))
                    chunk_text=text[start_ind:end_ind]
                    chunk_source=document.source
                    chunk_file_type=document.file_type
                    chunk_index=chunk_ind
                    chunk_ind+=1
                    chunking_strategy="structure"
                    metadata = document.metadata.copy()
                    metadata["start_char_in_section"] = start_ind
                    metadata["end_char_in_section"] = end_ind
                    metadata["heading"] = section["heading"]
                    metadata["heading_level"] = section["heading_level"]
                    metadata["heading_path"] = section["heading_path"].copy()
                    metadata["section_part"] = section_number
                    section_number+=1
        
                    c = Chunk(
                        text=chunk_text,
                        source=chunk_source,
                        file_type=chunk_file_type,
                        chunk_index=chunk_index,
                        chunking_strategy=chunking_strategy,
                        metadata=metadata,
                    )
                    chunks.append(c)
                    if end_ind == len(text):
                        break

            else:
                chunk_text=section["text"]
                chunk_source=document.source
                chunk_file_type=document.file_type
                chunk_index=chunk_ind
                chunk_ind+=1
                chunking_strategy="structure"
                metadata = document.metadata.copy()
                metadata["heading"] = section["heading"]
                metadata["heading_level"] = section["heading_level"]
                metadata["heading_path"] = section["heading_path"].copy()

                c = Chunk(
                        text=chunk_text,
                                        source=chunk_source,
                                        file_type=chunk_file_type,
                                        chunk_index=chunk_index,
                                        chunking_strategy=chunking_strategy,
                                        metadata=metadata,
                                    )
                chunks.append(c)

        return chunks
