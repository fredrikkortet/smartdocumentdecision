# **What**
Build an agent that reads an entire document, uses a user-editable context.md to understand preferences, 
and decides whether the end user must read the whole document or whether the extracted key info is sufficient with reason, 
confidence, and a structured output.

# **Diagram Explanation**

### **1. User Layer**
The user uploads any document (PDF, DOCX, TXT) and optionally customizes the agent’s behavior using a `context.md` file.

### **2. Extraction & Preprocessing Layer**
The backend extracts 100% of the text, normalizes formatting, removes boilerplate, and splits the document into intelligent overlapping chunks.

### **3. AI Processing Layer**
Each chunk is processed by an LLM to extract:
- Key information  
- Micro-summaries  
- Topic relevance indicators  

These are aggregated and passed to a document-level reasoning step.

### **4. Decision Engine**
Using user preferences from `context.md`, the system decides:
- Should the user read the full document?
- Is the key information enough?
- Is the document irrelevant?

### **5. Output Layer**
A structured JSON result is returned and rendered beautifully in the UI.

