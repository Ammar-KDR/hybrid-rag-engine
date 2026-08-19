from rag.ingestion.model import Document, Chunk


class FixedChunker:
    def __init__(self,chunk_size: int = 1000,overlap: int = 150,):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be a positive integer")
        elif overlap < 0 or overlap >= chunk_size:
            raise ValueError("overlap must be a non-negative integer less than chunk_size")
        self.chunk_size = chunk_size
        self.overlap = overlap
        
        

    def chunk(self, document: Document) -> list[Chunk]:
        text = document.text
        chunk_ind=0
        if len(text) == 0:
            return []
        step_size = self.chunk_size - self.overlap
        chunks = []
        for i in range(0,len(text),step_size):
            
            start_ind=i
            end_ind=i+self.chunk_size
            if end_ind>len(text):
                end_ind=len(text)
            chunk_text=text[start_ind:end_ind]
            chunk_source=document.source
            chunk_file_type=document.file_type
            chunk_index=chunk_ind
            chunk_ind+=1
            chunking_strategy="fixed"
            metadata = document.metadata.copy()
            metadata["start_char"] = start_ind
            metadata["end_char"] = end_ind

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
        return chunks





            


