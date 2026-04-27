# GRAVITYbot: A Forum Summary LLM Bot

An LLM bot that summarizes forum pages for the citizen science project [Gravity Spy](https://www.zooniverse.org/projects/zooniverse/gravity-spy).

## Description

GRAVITYbot:

1. Summarizes ["Talk" forum pages](https://www.zooniverse.org/projects/zooniverse/gravity-spy/talk) of Gravity Spy
2. Summarizes [aLOG forum posts](https://alog.ligo-la.caltech.edu/aLOG/) of LIGO's LLO and LHO lab locations

Gravity Spy is a citizen science project that classifies glitches occurring in The Laser Interferometer Gravitational-Wave Observatory (LIGO) sensor data. This project summarizes citizen science communication and day-to-day science and engineering updates. The objective is to streamline communication between distributed citizen scientists and LIGO scientists about classification issues surrounding gravitational wave data.

### Primary Tasks

1. Summarizing Talk pages for LIGO scientists
2. Summarizing Talk pages for citizen scientists
3. Logging dynamics of citizen science learning through automated weekly or sub-weekly updates

NOTICE: A somewhat related project is under development for a Gravity Spy chatbot. This project and the chatbot will be RAG-based using a central database that provides relevant scientific, engineering, and linguistic context.

### Possible Future Tasks

- RAG-based retrieval for contextual responses

## Getting Started

### Dependencies

- Python 3.10+
- `openai` (Azure OpenAI SDK)
- `pandas`
- `python-dotenv`
- `panoptes-client`
- `pytz`
- `feedparser`
- `beautifulsoup4`
- `markdown`

Install dependencies:
```bash
pip install openai pandas python-dotenv panoptes-client pytz feedparser beautifulsoup4 markdown
```

### Environment Configuration

Create a `.env` file in the project root with the following variables:

```bash
# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=<your-azure-openai-key>
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com
AZURE_OPENAI_API_VERSION=2025-01-01-preview
AZURE_OPENAI_DEPLOYMENT=<your-deployment-name>
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=<your-embedding-deployment>  # For future RAG

# LLM Parameters (optional - these are the defaults)
# GRAVITYBOT_LLM_TEMPERATURE=0.8
# GRAVITYBOT_LLM_MAX_TOKENS=4096

# Zooniverse/Panoptes Configuration
PANOPTES_SLUG=zooniverse/gravity-spy
PANOPTES_USER=<zooniverse-username>
PANOPTES_PASS=<zooniverse-password>
PANOPTES_ID=<your-panoptes-user-id>

# SMTP / Email Configuration
SMTP_HOST=<smtp-server>
SMTP_USER=<smtp-username>
SMTP_PASS=<smtp-password>
SMTP_FROM=<sender-email>
SMTP_TO=<recipient-email-or-comma-separated-list>

# Runtime Options
GRAVITYBOT_DRY_RUN=true  # Set to "false" for production

# Custom Paths (optional - defaults to _data/ and _output/ in project root)
# GRAVITYBOT_DATA_FOLDER_PATH=/path/to/data
# GRAVITYBOT_OUTPUT_FOLDER_PATH=/path/to/output
```

### Project Structure

```
GRAVITYbot/
├── config.py                      # Centralized configuration
├── _src/
│   ├── llm_client.py              # Azure OpenAI client abstraction
│   ├── alog_feed.py               # aLOG RSS feed fetching
│   ├── zooniverse.py              # Zooniverse Talk data fetching and posting
│   ├── prompts.py                 # LLM prompt templates
│   ├── emails.py                  # Email sending
│   ├── utils.py                   # Text cleaning utilities
│   ├── run_all.py                 # Main entry point (runs both pipelines)
│   ├── talk_summary.py            # Talk-only summary script
│   └── alog_summary.py            # aLOG-only summary script
├── _data/
│   ├── talk_posts.csv             # Zooniverse Talk export (canonical)
│   ├── talk_posts_raw.json        # Raw Zooniverse export (debug, overwritten)
│   ├── aLOG_RSS.csv               # aLOG entries (canonical, accumulates)
│   ├── aLOG_raw_LHO.xml           # Raw LHO RSS feed (debug, overwritten)
│   └── aLOG_raw_LLO.xml           # Raw LLO RSS feed (debug, overwritten)
├── _output/
│   ├── last_talk_summary.md       # Latest Talk summary
│   ├── last_lho_alog_summary.md   # Latest LHO aLOG summary
│   ├── last_llo_alog_summary.md   # Latest LLO aLOG summary
│   ├── llm_talk.log               # LLM call log for Talk summary
│   ├── llm_alog_lho.log           # LLM call log for LHO summary
│   └── llm_alog_llo.log           # LLM call log for LLO summary
├── test/
│   └── test_openai_access.py      # API connectivity test
├── .env                           # Configuration (not in repo)
├── Dockerfile                     # Container definition
├── docker_notes.txt               # Docker/cron usage guide
└── README.md
```

### Dry Run Mode

To test the pipeline without external API calls or posting, set:

```bash
GRAVITYBOT_DRY_RUN=true
```

In dry run mode:
- Data fetching is **skipped** (uses existing files in `_data/`)
- Date ranges are derived from the data itself (useful for testing with old data)
- LLM summaries are generated and saved to `_output/`
- Emails are **not** sent
- Zooniverse posts are **not** created

This is useful for testing changes without affecting production systems or consuming API quotas.

### Running the Project

1. **Test Azure connectivity:**
   ```bash
   python test/test_openai_access.py
   ```

2. **Run full summary (Talk + aLOG):**
   ```bash
   python _src/run_all.py
   ```

3. **Run Talk summary only:**
   ```bash
   python _src/talk_summary.py
   ```

4. **Run aLOG summary only:**
   ```bash
   python _src/alog_summary.py
   ```

### Docker Usage

See `docker_notes.txt` for Docker build/run commands and cron configuration.

### Customization

Prompt templates are defined in `_src/prompts.py`. See that file for instructions on creating or modifying prompts.

LLM parameters can be adjusted via environment variables (`GRAVITYBOT_LLM_TEMPERATURE`, `GRAVITYBOT_LLM_MAX_TOKENS`) or passed as arguments to `llm_client.generate()`.

## Help

This project uses Azure OpenAI via university Azure credits. If running locally with your own Azure subscription, be mindful of token usage and associated costs.

For issues or questions, contact the active Gravity Spy lab members or the maintainers listed below.

## Authors

Initial development by Alexander O. Smith as part of employment for Gravity Spy. Questions can be directed to aosmith@syr.edu or active Gravity Spy lab members.

## License

This project is licensed under an MIT "Expat" License. See the LICENSE.md file for details.

## Acknowledgments

We begin by acknowledging with respect the Onondaga Nation, Central Fire of the Haudenosaunee Confederacy, on whose ancestral lands Syracuse now stands. We are mindful that the technology that makes this project possible comes from mineral extraction by multinational corporations, which decimate and displace Indigenous peoples and their lands all over the world.

Additionally, Alexander would like to thank Gabriel Davila-Campos and Una Joh for advice and initial guidance in development.

## Backlog

- [ ] Make project pip-installable (pyproject.toml) to eliminate sys.path manipulation
- [ ] Implement RAG for contextual retrieval
- [ ] Add unit tests for core functions
