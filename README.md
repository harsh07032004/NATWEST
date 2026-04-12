# Talk to Data

## Overview
"Talk to Data" is an intelligent, self-service analytics platform designed to democratize access to business data. The project solves the problem of data gatekeeping by allowing non-technical users to query complex datasets using simple natural language. Instead of navigating complicated BI tools, target users (ranging from beginners to executives) can simply ask questions and receive deterministic financial metrics paired with tailored, persona-driven explanations.

## Features
- **Conversational Analytics:** Chat interface that accepts natural language queries.
- **Persona-Driven Explanations:** Real-time LLM-driven modifications of summaries adapting to Beginner, Analyst, Executive, and other personas.
- **Deterministic Math Engine:** Pure mathematical computation using statistical processing (Pandas) decoupled from LLM hallucinations.
- **Multi-Intent Analysis:** Supports identifying multiple intents (e.g. Descriptive + Diagnostic) in a single query and merging the execution results.
- **Dynamic Dataset Pipeline:** Extensible execution engine parameterized to evaluate static CSV files or dynamically generated user-uploaded datasets.
- **Data Security Guardrails:** Includes a localized execution sandbox that strictly blocks Local File Inclusion (LFI), system state tampering, and LLM prompt/jailbreak injection natively.
- **Microservices Architecture:** Fully decoupled systems enabling parallel execution, graceful error handling, and robust scalability.
- **Graceful Fallbacks:** Automated mock-data adapters ensure the UI never crashes even if backend connections fail.

## Architecture Overview
The system relies on a secure **3-pillar Microservice Monorepo** pattern:
1. **React Frontend (Port 3000):** A highly responsive, Vite-powered UI handling the chat view, visualizations, and Gemini-based persona summaries. 
2. **Node.js Orchestrator (Port 5000):** The central nervous system. It compiles natural language (via Groq API) into a strict Data Blueprint Execution Plan and handles API routing, MongoDB tracking, and graceful degradation.
3. **Python FastAPI Engine (Port 8000):** A deterministic execution layer. It receives the JSON Execution Plan from the Orchestrator, dynamically injects user-uploaded or global CSV data safely avoiding path traversal attacks, and returns pure numbers/arrays without any text generation.

## Tech Stack
- **Frontend:** React 19, TypeScript, Vite, Tailwind CSS, Lucide Icons, Framer Motion
- **Backend:** Node.js, Express.js, MongoDB (Mongoose)
- **Math Engine:** Python, FastAPI, Pandas, Scikit-learn, Uvicorn
- **AI Models:** Groq SDK (Llama 3.3 for Execution Plan), Google Generative AI (Gemini 2.5 Flash for Persona Text Gen)

## Setup Instructions
Follow these commands to seamlessly boot the entire monorepo locally.

**1. Clone the repository and configure environments:**
\`\`\`bash
# Create Backend .env
cd backend
cp .env.example .env
# Edit .env and supply your MONGODB_URI and GROQ_API_KEY

# Create Execution Engine .env
cd ../execution_engine
cp .env.example .env

# Configure Frontend
# Set up a .env inside `frontend/` containing your VITE_GEMINI_API_KEY
\`\`\`

**2. Install Dependencies:**
\`\`\`bash
# Backend dependencies
cd backend
npm install

# Frontend dependencies
cd ../frontend
npm install

# Execution engine dependencies
cd ../execution_engine
pip install -r requirements.txt
\`\`\`

**3. Run the Global Startup Script:**
Ensure you are at the project root folder.
\`\`\`bash
scripts\start_all.bat
\`\`\`
*(This master script automatically opens 3 partitioned CMD windows booting all services in parallel).*

## Usage Examples
To explore the system, type the following natural language questions into the Chat UI:
- **Descriptive:** *"What is our current monthly spending?"*
- **Comparative:** *"How did February revenue compare against January?"*
- **Diagnostic:** *"Why did our costs spike so dramatically last month?"*
- **Predictive:** *"Based on the trajectory, what will the spending look like next week?"*

## Limitations & Future Improvements
While structurally complete, there are several open areas for optimization:
- **Database Reliance:** The Python Math Engine natively targets flat files (`data/` or `uploads/`). Future iterations should securely implement live read-only SQL queries via DuckDB/Snowflake pipelines mapping database configurations into the Execution Plan schema mapping.
- **Graphing Interactivity:** Chart definitions currently rely on fixed visual structures and simple fallback tables; deeper Recharts implementations are planned to support complex multi-axis combinations.
- **User Authentication:** No hard session JWTs or OAuth systems are configured yet, relying purely on mock session states.
