# Docs-ForAI

![Docs-ForAI Banner](https://huggingface.co/datasets/Iruziky/docs-forai-data/resolve/main/Docs-ForAI_banner.png)

**Docs-ForAI: Open-source RAG context for AI Agent development.**
*Eliminating LLM hallucinations by providing real-time, verified documentation indexing for the AI Agent ecosystem.*

---

### Project Status: MVP (Proof of Concept)
The project is currently in its MVP stage. Users can locally scrape, clean, and index Python documentations to use as an MCP (Model Context Protocol) tool in IDEs like Claude Desktop or Cursor. To ensure zero cost and privacy, we use **LanceDB** for local storage and the **`all-MiniLM-L6-v2`** model for local embeddings (CPU-based).

### Current Features & Mechanics
- **Pre-indexed Libraries:** We provide ready-to-use configurations and indices for the most critical AI Agent frameworks:
    1.  [LangGraph](https://langchain-ai.github.io/langgraph/)
    2.  [CrewAI](https://docs.crewai.com/)
    3.  [PydanticAI](https://ai.pydantic.dev/)
    4.  [AutoGen](https://microsoft.github.io/autogen/docs/Getting-Started/)
    5.  [LlamaIndex](https://docs.llamaindex.ai/en/stable/)
    6.  [OpenAI Swarm](https://github.com/openai/swarm)
    7.  [Phidata](https://docs.phidata.com/introduction)
    8.  [Haystack](https://docs.haystack.deepset.ai/docs/intro)
    9.  [PraisonAI](https://docs.praison.ai/)
    10. [LiteLLM](https://docs.litellm.ai/docs/)
- **Universal Ingestion:** While our focus is Python AI Agents, you can index any documentation URL (any language or topic).
- **Smart Caching:** We use a simple cache system (`ingestion_cache.json`) to skip already processed documentations.
  *Note: To force a re-index, manually remove the entry from the JSON array.*
- **Manual Updates:** Documentation updates are not yet automatic.

### How to use the MVP
To test the current version, follow these steps:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/iruziky/Docs-ForAI.git
   cd Docs-ForAI
   ```

2. **Switch to the MVP branch:**
   ```bash
   git checkout feat/mvp-local-index
   ```

3. **Setup the environment:**
   Using [uv](https://github.com/astral-sh/uv) (recommended):
   ```bash
   pip install uv
   uv venv
   uv pip install -e .
   ```

4. **Download Pre-indexed Data (Optional):**
   To avoid scraping everything from scratch, you can download the pre-computed indices from Hugging Face:
   ```bash
   uv run setup
   ```
   *This will download the `lancedb_data/` folder to your local project.*

5. **Configure your target:**
   Edit `config.json` and add the documentation URLs you wish to index or keep current ones.

6. **Run the Ingestion (if adding new docs):**
   ```bash
   uv run ingest
   ```

7. **Add to your MCP Settings:**
   To get the exact JSON block for your configuration, run:
   ```bash
   uv run config
   ```
   
   Copy the output and follow the instructions for your IDE below:

   #### 🤖 Claude Desktop
   1. Open Claude Desktop.
   2. Open the configuration file:
      - **macOS:** `~/Library/Application\ Support/Claude/claude_desktop_config.json`
      - **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
   3. Paste the JSON block inside the `mcpServers` object.
   4. Restart Claude Desktop.

   #### 🚀 Cursor
   1. Open Cursor Settings (**Ctrl+Shift+J** or **Cmd+Shift+J**).
   2. Go to **Features** -> **MCP**.
   3. Click **+ Add New MCP Server**.
   4. Set the Type to `command` and use the values provided by `uv run config`.
      - *Name:* `Docs-ForAI`
      - *Command:* `uv`
      - *Arguments:* (Paste the arguments list from the output)

   #### 💻 VS Code (via Cline/Goose/Roo-Code)
   VS Code doesn't support MCP natively yet. You must use an extension like [Cline](https://github.com/cline/cline), [Goose](https://github.com/block/goose), or [Roo-Code](https://github.com/RooVetS/Roo-Code).
   1. Open the extension's settings.
   2. Look for the **MCP Config** or **mcp_config.json** section.
   3. Add the JSON block provided by `uv run config`.

   ---
   > ⚠️ **Disclaimer:** IDE interfaces and MCP support change rapidly. These instructions are based on the latest known versions and might vary. Always check your IDE's official documentation or MCP extension settings if these steps don't match your current UI.

### Future Roadmap

* **Robust Pipeline:** Transition to **Llama-index** for more sophisticated data parsing and chunking.
* **MCP Routing:** For libraries that already provide an official MCP server, Docs-ForAI will act as a **router**, connecting the LLM directly to the official tool instead of just providing RAG context.
* **Mass Pre-indexing:** Scale the availability of high-quality indices for all major AI Agent frameworks.
* **Automated Sync:** Implement a scheduler to keep documentations up-to-date automatically.
* **Distributed & Ethical Scraping:** Implement parallel scraping across different domains to speed up ingestion while strictly avoiding DoS-like behavior on a single documentation site.
* **Hybrid Indexing:** Separate pre-processed indices (high-performance cloud embeddings) from user-generated indices (free local embeddings).

---

### 🧠 Technical Specs
- **Vector Store:** LanceDB
- **Embedding Model:** `sentence-transformers/all-MiniLM-L6-v2` (Running locally on CPU)
- **Content:** This dataset contains only the computed indices (`lancedb_data/`). Raw text files (`docs_input/`) are not included to keep the download efficient.

---

### ⚖️ Legal Disclaimer
Docs-ForAI is a research and productivity tool. We do not own the documentation content. All rights belong to the respective owners. Our goal is to enhance the developer experience by providing better context to AI models. If you are a copyright holder and want your documentation removed, please open an issue.
