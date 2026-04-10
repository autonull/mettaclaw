## MeTTaClaw 2

<img width="362" alt="image" src="https://github.com/user-attachments/assets/197d745f-1562-4d31-88c2-b813a56ccbf1" />

An agentic AI system implemented in MeTTa, guided by the MeTTaClaw proposal and an agent core inspired by Nanobot.
Beyond basic tool use, it features embedding-based long-term memory represented entirely in MeTTa AtomSpace format.

Long-term memory is deliberately maintained by the agent via `(remember string)` for adding memory items and `(query string)` for querying related memories.
The agent can learn and apply new skills and declarative knowledge through the use of memory items.

In addition, an initial set of OpenClaw-like tools is implemented, including web search, file modification, communication channels, and access to the operating system shell and its associated tools.

Simplicity of design, ease of prototyping, ease of extension, and transparent implementation in MeTTa were the primary design criteria.
The agent core comprises approximately 200 lines of code.

**Special Features**

- MeTTaClaw uses a token-efficient agentic loop, enabling low-cost long-term operation and embodiment in domains that require real-time learning and decision-making.

- The agent can learn to represent its memories in different ways, including such that allow other Hyperon components to operate on the same memories within the same Atomspace. Each memory item is stored as a triplet `(timestamp, atom, embedding)`, while the agent remains flexible in choosing the representation for the atom itself. Consequently, the agent is not hardcoded to any particular memory representation, and different formats can co-exist in the same atom space.

The following example demonstrates learning and decision-making in a textually represented grid-world environment adapted from [NACE](https://github.com/patham9/NACE):

![mettaclaw_in_nace_world](https://github.com/user-attachments/assets/c6c01839-234d-4505-baf6-4f2f3787c7b9)

This project also aims to explore the potential of Agentic Physical AI, a ROS2 package for mobile robots with manipulators is underway.

---

## Quick Start

### Step 1: Install Dependencies

First, get [SWI-Prolog](https://www.swi-prolog.org/). Then:

```bash
git clone https://github.com/trueagi-io/PeTTa
cd PeTTa
mkdir -p repos && git clone https://github.com/patham9/mettaclaw repos/mettaclaw
cd repos/mettaclaw
```

### Step 2: Configure Your LLM Provider

MeTTaClaw supports 100+ LLM providers. Choose one:

#### Option A: OpenAI (GPT-4, GPT-3.5)

```bash
export OPENAI_API_KEY="sk-..."
python run.py
```

Get API key: https://platform.openai.com/api-keys

#### Option B: Anthropic (Claude)

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
python run.py
```

Get API key: https://console.anthropic.com/settings/keys

#### Option C: Ollama (Local, Free)

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a model
ollama pull llama3

# Run MeTTaClaw
python run.py
```

Ollama auto-detects at `http://localhost:11434`

#### Option D: Use a .env File

Create a `.env` file in the project root:

```bash
# .env
ANTHROPIC_API_KEY="sk-ant-..."
# or
OPENAI_API_KEY="sk-..."
# or
OLLAMA_API_BASE="http://localhost:11434"
```

Then just run:
```bash
python run.py
```

### Step 3: Run

```bash
python run.py
```

Or with a custom script:
```bash
python run.py my_script.metta
```

---

## Configuration

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |
| `ANTHROPIC_API_KEY` | Anthropic API key | `sk-ant-...` |
| `OLLAMA_API_BASE` | Ollama server URL | `http://localhost:11434` |
| `OPENROUTER_API_KEY` | OpenRouter API key | `...` |
| `GROQ_API_KEY` | Groq API key | `gsk_...` |
| `TOGETHER_API_KEY` | Together AI key | `...` |
| `GOOGLE_API_KEY` | Google AI key | `...` |
| `AWS_ACCESS_KEY_ID` | AWS access key | `...` |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | `...` |
| `AZURE_API_KEY` | Azure OpenAI key | `...` |
| `LLM_PROVIDER` | Preferred provider | `anthropic` |
| `LLM_MODEL` | Override default model | `anthropic/claude-sonnet-4-20250514` |

### Supported Providers

| Provider | Env Variable | Default Model | Get Key |
|----------|-------------|---------------|---------|
| **OpenAI** | `OPENAI_API_KEY` | `openai/gpt-4o` | https://platform.openai.com |
| **Anthropic** | `ANTHROPIC_API_KEY` | `anthropic/claude-opus-4-20250514` | https://console.anthropic.com |
| **Ollama** | (none, local) | `ollama/llama3` | https://ollama.ai |
| **OpenRouter** | `OPENROUTER_API_KEY` | `openrouter/anthropic/claude-3-opus` | https://openrouter.ai |
| **Groq** | `GROQ_API_KEY` | `groq/llama3-70b-8192` | https://console.groq.com |
| **Together AI** | `TOGETHER_API_KEY` | `together_ai/meta-llama/Llama-3-70b` | https://api.together.ai |
| **Google** | `GOOGLE_API_KEY` | `google/gemini-pro` | https://console.cloud.google.com |
| **AWS Bedrock** | `AWS_ACCESS_KEY_ID` | `bedrock/anthropic.claude-3-opus` | https://aws.amazon.com |
| **Azure** | `AZURE_API_KEY` | `azure/gpt-4` | https://portal.azure.com |

### MeTTa Configuration

Create a `config.metta` file for MeTTa-based configuration:

```metta
;; LLM Configuration
(configure provider "anthropic")
(configure LLM "anthropic/claude-opus-4-20250514")
(configure maxOutputToken 8192)
(configure reasoningMode "medium")

;; Loop Configuration
(configure maxNewInputLoops 50)
(configure maxWakeLoops 1)
(configure sleepInterval 1)
(configure wakeupInterval 600)

;; Memory Configuration
(configure memorySize 1000)
(configure memorySimilarityThreshold 0.75)
```

---

## Usage

### Auto-install/Run

If PeTTa is already installed and the latest version pulled (v1.0.2 or latest commit), then, running the following MeTTa file from the root folder, installs and runs MeTTaClaw (assuming API key is set):

```metta
!(import! &self (library lib_import))
!(git-import! "https://github.com/patham9/mettaclaw.git")
!(import! &self (library mettaclaw lib_mettaclaw))

!(mettaclaw)
```

### Command Line

```bash
# Run with default script
python run.py

# Run with custom script
python run.py my_script.metta

# Run with specific provider
OPENAI_API_KEY="sk-..." python run.py

# Verbose output
METTACLAW_VERBOSE=true python run.py
```

### Docker/Podman

Build and run MeTTaClaw in a container (no need to install SWI-Prolog):

```bash
# 1. Build the Docker image
./run.sh build

# 2. Run (set your API key)
OPENAI_API_KEY="sk-..." ./run.sh
# Or with a custom script:
OPENAI_API_KEY="sk-..." ./run.sh run myscript.metta
```

Other commands:
```bash
./run.sh start    # Interactive chat mode
./run.sh sh     # Drop into shell for debugging
./run.sh clean   # Remove image
./run.sh status  # Check image/container status
```

Configure LLM provider at runtime:
```bash
ANTHROPIC_API_KEY="sk-ant-..." ./run.sh     # Use Claude
OLLAMA_API_BASE="http://localhost:11434" ./run.sh  # Use Ollama
```

---

## Examples

### Basic Agent Loop

```metta
!(import! &self (library lib_import))
!(import! &self (library mettaclaw lib_mettaclaw))

!(mettaclaw)
```

### Custom Configuration

```metta
!(import! &self (library lib_import))
!(import! &self (library mettaclaw lib_mettaclaw))

;; Set custom LLM provider
(configure provider "groq")
(configure LLM "groq/llama3-70b-8192")
(configure maxOutputToken 4096)

!(mettaclaw)
```

### Memory Operations

```metta
;; Add to memory
(remember "The sky is blue")

;; Query memory
(query "What color is the sky?")

;; Use in agent loop
!(mettaclaw)
```

---

## Illustrations

**Long-Term Memory Recall:**

<img width="638" height="125" alt="image" src="https://github.com/user-attachments/assets/0d4817ed-e743-4e44-8bd4-a10e27ea6380" />

**Tool use:**

<img width="1323" height="188" alt="image" src="https://github.com/user-attachments/assets/18ef19c4-010a-4c94-84ce-bb49277dccfc" />

**Shell output of the actual invocation of the generated MeTTa code:**

<img width="416" height="486" alt="image" src="https://github.com/user-attachments/assets/f5b27205-cdb2-47e7-821a-ffd93b3dd7c6" />

**System also added it into its Atom Space storage (embedding vector omitted):**

<img width="379" height="69" alt="image" src="https://github.com/user-attachments/assets/6aa59deb-33b4-42b9-a535-ae153b4b7a18" />

---

## Documentation

- [CONFIG.md](CONFIG.md) - Comprehensive configuration guide
- [LITELLM_CONFIG.md](LITELLM_CONFIG.md) - LiteLLM provider documentation
- [LITELLM_SUMMARY.md](LITELLM_SUMMARY.md) - Implementation summary

## Testing

```bash
# Run configuration tests
python test_litellm.py

# Test configuration loading
python mettaclaw_config.py
```

## Troubleshooting

### "No API key found"
- Set the appropriate environment variable for your provider
- Or create a `.env` file with your API key

### "Invalid model name"
- Use format: `provider/model-name`
- Check provider documentation for exact model names

### "Ollama connection failed"
- Ensure Ollama is running: `ollama serve`
- Check URL: `export OLLAMA_API_BASE="http://localhost:11434"`

### More help
See [CONFIG.md](CONFIG.md) for detailed troubleshooting.

## License

[Your License Here]
