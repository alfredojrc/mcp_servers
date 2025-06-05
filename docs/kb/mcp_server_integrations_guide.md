# MCP Server Integrations Guide

This document provides a curated list of Model Context Protocol (MCP) servers, focusing on integrations relevant to our project. The primary source for this information is the [Official MCP Servers List](https://github.com/modelcontextprotocol/servers) and its "Official Integrations" section.

## Proxy, Gateway, and Orchestration MCP Servers

Servers that can act as proxies, gateways, or help in orchestrating calls to other services or tools.

*   <img height="12" width="12" src="https://agentrpc.com/favicon.ico" alt="AgentRPC Logo" /> **[AgentRPC](https://github.com/agentrpc/agentrpc)** - Connect to any function, any language, across network boundaries using [AgentRPC](https://www.agentrpc.com/). (Could act as a proxy/bridge).
*   <img height="12" width="12" src="https://cdn.chiki.studio/brand/logo.png" /> **[Chiki StudIO](https://chiki.studio/galimybes/mcp/)** - Create your own configurable MCP servers purely via configuration (no code), with instructions, prompts, and tools support. (Might be used to proxy or adapt).
*   <img height="12" width="12" src="https://unifai.network/favicon.ico" alt="UnifAI Logo" /> **[UnifAI](https://github.com/unifai-network/unifai-mcp-server)** - Dynamically search and call tools using [UnifAI Network](https://unifai.network). (Could act as a proxy/aggregator).
*   <img height="12" width="12" src="https://www.veyrax.com/favicon.ico" alt="VeyraX Logo" /> **[VeyraX](https://github.com/VeyraX/veyrax-mcp)** - Single tool to control all 100+ API integrations, and UI components. (Aggregator/proxy).
*   **[WayStation](https://github.com/waystation-ai/mcp)** - Universal MCP server to connect to popular productivity tools such as Notion, Monday, AirTable, and many more. (Acts as a universal connector/proxy).
    *   *Note: Listed under "Official Integrations" in the source README.*
*   <img height="12" width="12" src="https://www.make.com/favicon.ico" alt="Make Logo" /> **[Make](https://github.com/integromat/make-mcp-server)** - Turn your [Make](https://www.make.com/) scenarios into callable tools for AI assistants. (Workflow orchestration).
*   <img height="12" width="12" src="https://cdn.zapier.com/zapier/images/favicon.ico" alt="Zapier Logo" /> **[Zapier](https://zapier.com/mcp)** - Connect your AI Agents to 8,000 apps instantly. (Workflow automation and integration proxy).

## Financial, Trading, and Exchange MCP Servers

Servers related to financial data, cryptocurrency exchanges, payment processing, and accounting.

*   <img height="12" width="12" src="https://invoxx-public-bucket.s3.eu-central-1.amazonaws.com/frontend-resources/adfin-logo-small.svg" alt="Adfin Logo" /> **[Adfin](https://github.com/Adfin-Engineering/mcp-server-adfin)** - The only platform you need to get paid - all payments in one place, invoicing and accounting reconciliations with [Adfin](https://www.adfin.com/).
*   <img height="12" width="12" src="https://www.bankless.com/favicon.ico" alt="Bankless Logo" /> **[Bankless Onchain](https://github.com/bankless/onchain-mcp)** - Query Onchain data, like ERC20 tokens, transaction history, smart contract state.
*   <img height="12" width="12" src="https://bicscan.io/favicon.png" alt="BICScan Logo" /> **[BICScan](https://github.com/ahnlabio/bicscan-mcp)** - Risk score / asset holdings of EVM blockchain address (EOA, CA, ENS) and even domain names.
*   <img height="12" width="12" src="https://dexpaprika.com/favicon.ico" alt="DexPaprika Logo" /> **[DexPaprika (CoinPaprika)](https://github.com/coinpaprika/dexpaprika-mcp)** - Access real-time DEX data, liquidity pools, token information, and trading analytics across multiple blockchain networks with [DexPaprika](https://dexpaprika.com) by CoinPaprika.
*   <img height="12" width="12" src="https://fewsats.com/favicon.svg" alt="Fewsats Logo" /> **[Fewsats](https://github.com/Fewsats/fewsats-mcp)** - Enable AI Agents to purchase anything in a secure way using [Fewsats](https://fewsats.com).
*   <img height="12" width="12" src="https://financialdatasets.ai/favicon.ico" alt="Financial Datasets Logo" /> **[Financial Datasets](https://github.com/financial-datasets/mcp-server)** - Stock market API made for AI agents.
*   <img height="12" width="12" src="https://www.mercadopago.com/favicon.ico" alt="MercadoPago Logo" /> **[Mercado Pago](https://mcp.mercadopago.com/)** - Mercado Pago's official MCP server.
*   <img height="12" width="12" src="https://developer.paddle.com/favicon.svg" alt="Paddle Logo" /> **[Paddle](https://github.com/PaddleHQ/paddle-mcp-server)** - Interact with the Paddle API. Manage product catalog, billing and subscriptions, and reports.
*   <img height="12" width="12" src="https://secure.pagos.ai/favicon.svg" alt="Pagos Logo" /> **[Pagos](https://github.com/pagos-ai/pagos-mcp)** - Interact with the Pagos API. Query Credit Card BIN Data with more to come.
*   <img height="12" width="12" src="https://www.paypalobjects.com/webstatic/icon/favicon.ico" alt="PayPal Logo" /> **[PayPal](https://mcp.paypal.com)** - PayPal's official MCP server.
*   <img height="12" width="12" src="https://www.ramp.com/favicon.ico" /> **[Ramp](https://github.com/ramp-public/ramp-mcp)** - Interact with [Ramp](https://ramp.com)'s Developer API to run analysis on your spend and gain insights leveraging LLMs.
*   <img height="12" width="12" src="https://stripe.com/favicon.ico" alt="Stripe Logo" /> **[Stripe](https://github.com/stripe/agent-toolkit)** - Interact with Stripe API.
*   <img height="12" width="12" src="https://thirdweb.com/favicon.ico" alt="Thirdweb Logo" /> **[Thirdweb](https://github.com/thirdweb-dev/ai/tree/main/python/thirdweb-mcp)** - Read/write to over 2k blockchains, enabling data querying, contract analysis/deployment, and transaction execution, powered by [Thirdweb](https://thirdweb.com/).
*   <img height="12" width="12" src="https://www.xero.com/favicon.ico" alt="Xero Logo" /> **[Xero](https://github.com/XeroAPI/xero-mcp-server)** - Interact with the accounting data in your business using our official MCP server.

## Linux, Code Execution, and Sandboxing MCP Servers

Servers providing capabilities for code execution, often in sandboxed (Linux-based) environments.

*   <img height="12" width="12" src="https://e2b.dev/favicon.ico" alt="E2B Logo" /> **[E2B](https://github.com/e2b-dev/mcp-server)** - Run code in secure sandboxes hosted by [E2B](https://e2b.dev).
*   <img height="12" width="12" src="https://forevervm.com/icon.png" alt="ForeverVM Logo" /> **[ForeverVM](https://github.com/jamsocket/forevervm/tree/main/javascript/mcp-server)** - Run Python in a code sandbox.
*   <img height="12" width="12" src="https://riza.io/favicon.ico" alt="Riza logo" /> **[Riza](https://github.com/riza-io/riza-mcp)** - Arbitrary code execution and tool-use platform for LLMs by [Riza](https://riza.io).
    *   *Note: The "Community Servers" section lists more specific OS interactions like `Apple Script` and `Windows CLI`.*

## Kubernetes (K8s) MCP Servers

Servers for interacting with Kubernetes environments.

*   <img height="12" width="12" src="https://metoro.io/static/images/logos/Metoro.svg" /> **[Metoro](https://github.com/metoro-io/metoro-mcp-server)** - Query and interact with kubernetes environments monitored by Metoro.
    *   *Note: The "Community Servers" section of the source README has a more extensive list of Kubernetes-specific MCP servers, including `k8s-multicluster-mcp`, `Kubernetes`, `Kubernetes and OpenShift`, `mcp-k8s-go`.*

## Google & Google Cloud MCP Servers

Servers providing integration with Google services and Google Cloud Platform.

*   <img height="12" width="12" src="https://googleapis.github.io/genai-toolbox/favicons/favicon.ico" alt="MCP Toolbox for Databases Logo" /> **[MCP Toolbox for Databases](https://github.com/googleapis/genai-toolbox)** - Open source MCP server specializing in easy, fast, and secure tools for Databases. Supports AlloyDB, BigQuery, Bigtable, Cloud SQL (all Google Cloud products), Dgraph, MySQL, Neo4j, Postgres, Spanner, and more.
    *   *Note: The "Archived" Reference Servers list in the source README includes `Google Drive` and `Google Maps`. The "Community Servers" list includes `Google Calendar`, `Google Custom Search`, `Google Sheets`, `Google Tasks`, `Google Vertex AI Search`, and `Google Workspace`.*

## Vector Database & Semantic Search MCP Servers

Servers for interacting with vector databases, enabling semantic search and RAG capabilities.

*   <img height="12" width="12" src="https://www.datastax.com/favicon-32x32.png" alt="DataStax logo" /> **[Astra DB](https://github.com/datastax/astra-db-mcp)** - Comprehensive tools for managing collections and documents in a [DataStax Astra DB](https://www.datastax.com/products/datastax-astra) NoSQL database. (Astra DB can handle vector workloads).
*   <img height="12" width="12" src="https://trychroma.com/_next/static/media/chroma-logo.ae2d6e4b.svg" /> **[Chroma](https://github.com/chroma-core/chroma-mcp)** - Embeddings, vector search, document storage, and full-text search with the open-source AI application database.
*   <img height="12" width="12" src="https://www.elastic.co/favicon.ico" alt="Elasticsearch Logo" /> **[Elasticsearch](https://github.com/elastic/mcp-server-elasticsearch)** - Query your data in [Elasticsearch](https://www.elastic.co/elasticsearch). (Elasticsearch supports vector search).
*   <img height="12" width="12" src="https://www.meilisearch.com/favicon.ico" alt="Meilisearch Logo" /> **[Meilisearch](https://github.com/meilisearch/meilisearch-mcp)** - Interact & query with Meilisearch (Full-text & semantic search API). (Supports vector search).
*   <img height="12" width="12" src="https://memgraph.com/favicon.png" alt="Memgraph Logo" /> **[Memgraph](https://github.com/memgraph/mcp-memgraph)** - Query your data in [Memgraph](https://memgraph.com/) graph database. (Graph databases are often used with or adding vector capabilities).
*   <img height="12" width="12" src="https://milvus.io/favicon-32x32.png" /> **[Milvus](https://github.com/zilliztech/mcp-server-milvus)** - Search, Query and interact with data in your Milvus Vector Database.
*   <img height="12" width="12" src="https://www.mongodb.com/favicon.ico" /> **[MongoDB](https://github.com/mongodb-js/mongodb-mcp-server)** - Both MongoDB Community Server and MongoDB Atlas are supported. (MongoDB supports vector search).
*   <img height="12" width="12" src="https://needle-ai.com/images/needle-logo-orange-2-rounded.png" alt="Needle AI Logo" /> **[Needle](https://github.com/needle-ai/needle-mcp)** - Production-ready RAG out of the box to search and retrieve data from your own documents. (Likely uses a vector DB).
*   <img height="12" width="12" src="https://neo4j.com/favicon.ico" alt="Neo4j Logo" /> **[Neo4j](https://github.com/neo4j-contrib/mcp-neo4j/)** - Neo4j graph database server (schema + read/write-cypher) and separate graph database backed memory. (Neo4j supports vector search).
*   <img height="12" width="12" src="https://avatars.githubusercontent.com/u/54333248" /> **[Pinecone](https://github.com/pinecone-io/pinecone-mcp)** - [Pinecone](https://docs.pinecone.io/guides/operations/mcp-server)'s developer MCP Server assist developers in searching documentation and managing data within their development environment.
*   <img height="12" width="12" src="https://avatars.githubusercontent.com/u/54333248" /> **[Pinecone Assistant](https://github.com/pinecone-io/assistant-mcp)** - Retrieves context from your [Pinecone Assistant](https://docs.pinecone.io/guides/assistant/mcp-server) knowledge base.
*   <img height="12" width="12" src="https://qdrant.tech/img/brand-resources-logos/logomark.svg" /> **[Qdrant](https://github.com/qdrant/mcp-server-qdrant/)** - Implement semantic memory layer on top of the Qdrant vector search engine.
*   <img height="12" width="12" src="https://upstash.com/icons/favicon-32x32.png" alt="Upstash Logo" /> **[Upstash](https://github.com/upstash/mcp-server)** - Manage Redis databases and run Redis commands on [Upstash](https://upstash.com/) with natural language. (Redis can be used for vector storage/search).
*   **[Vectorize](https://github.com/vectorize-io/vectorize-mcp-server/)** - [Vectorize](https://vectorize.io) MCP server for advanced retrieval, Private Deep Research, Anything-to-Markdown file extraction and text chunking.

## Other Potentially Useful MCP Servers (Official Integrations)

This section includes other official integrations that might be broadly useful.

*   <img height="12" width="12" src="https://www.algolia.com/files/live/sites/algolia-assets/files/icons/algolia-logo-for-favicon.svg" alt="Algolia Logo" /> **[Algolia MCP](https://github.com/algolia/mcp-node)** - Algolia MCP Server exposes a natural language interface to query, inspect, and manage Algolia indices and configs.
*   <img height="12" width="12" src="https://apify.com/favicon.ico" alt="Apify Logo" /> **[Apify](https://github.com/apify/actors-mcp-server)** - [Actors MCP Server](https://apify.com/apify/actors-mcp-server): Use 3,000+ pre-built cloud tools to extract data from websites, e-commerce, social media, search engines, maps, and more.
*   <img height="12" width="12" src="https://a0.awsstatic.com/libra-css/images/site/fav/favicon.ico" alt="AWS Logo" /> **[AWS](https://github.com/awslabs/mcp)** - Specialized MCP servers that bring AWS best practices directly to your development workflow.
*   <img height="12" width="12" src="https://cdn-dynmedia-1.microsoft.com/is/content/microsoftcorp/acom_social_icon_azure" alt="Microsoft Azure Logo" /> **[Azure](https://github.com/Azure/azure-mcp)** - The Azure MCP Server gives MCP Clients access to key Azure services and tools like Azure Storage, Cosmos DB, the Azure CLI, and more.
*   <img height="12" width="12" src="https://browserbase.com/favicon.ico" alt="Browserbase Logo" /> **[Browserbase](https://github.com/browserbase/mcp-server-browserbase)** - Automate browser interactions in the cloud (e.g. web navigation, data extraction, form filling, and more).
*   <img height="12" width="12" src="https://cdn.simpleicons.org/cloudflare" /> **[Cloudflare](https://github.com/cloudflare/mcp-server-cloudflare)** - Deploy, configure & interrogate your resources on the Cloudflare developer platform (e.g. Workers/KV/R2/D1).
*   <img height="12" width="12" src="https://www.devhub.com/img/upload/favicon-196x196-dh.png" alt="DevHub Logo" /> **[DevHub](https://github.com/devhub/devhub-cms-mcp)** - Manage and utilize website content within the [DevHub](https://www.devhub.com) CMS platform.
*   <img height="12" width="12" src="https://exa.ai/images/favicon-32x32.png" alt="Exa Logo" /> **[Exa](https://github.com/exa-labs/exa-mcp-server)** - Search Engine made for AIs by [Exa](https://exa.ai).
*   <img height="12" width="12" src="https://firecrawl.dev/favicon.ico" alt="Firecrawl Logo" /> **[Firecrawl](https://github.com/mendableai/firecrawl-mcp-server)** - Extract web data with [Firecrawl](https://firecrawl.dev).
*   <img height="12" width="12" src="https://github.githubassets.com/assets/GitHub-Mark-ea2971cee799.png" /> **[Github](https://github.com/github/github-mcp-server)** - GitHub's official MCP Server.
*   <img height="12" width="12" src="https://www.heroku.com/favicons/favicon.ico" alt="Heroku Logo" /> **[Heroku](https://github.com/heroku/heroku-mcp-server)** - Interact with the Heroku Platform through LLM-driven tools for managing apps, add-ons, dynos, databases, and more.
*   <img height="12" width="12" src="https://static.hsinfrastatic.net/StyleGuideUI/static-3.438/img/sprocket/favicon-32x32.png" alt="HubSpot Logo" /> **[HubSpot](https://developer.hubspot.com/mcp)** - Connect, manage, and interact with [HubSpot](https://www.hubspot.com/) CRM data.
*   <img height="12" width="12" src="https://kagi.com/favicon.ico" alt="Kagi Logo" /> **[Kagi Search](https://github.com/kagisearch/kagimcp)** - Search the web using Kagi's search API.
*   <img height="12" width="12" src="https://avatars.githubusercontent.com/u/4792552?s=200&v=4" alt="Notion Logo" /> **[Notion](https://github.com/makenotion/notion-mcp-server#readme)** - This project implements an MCP server for the Notion API.
*   <img height="12" width="12" src="https://www.perplexity.ai/favicon.ico" alt="Perplexity Logo" /> **[Perplexity](https://github.com/ppl-ai/modelcontextprotocol)** - An MCP server that connects to Perplexity's Sonar API, enabling real-time web-wide research in conversational AI.
*   <img height="12" width="12" src="https://www.pulumi.com/images/favicon.ico" alt="Pulumi Logo" /> **[Pulumi](https://github.com/pulumi/mcp-server)** - Deploy and manage cloud infrastructure using [Pulumi](https://pulumi.com).
*   <img height="12" width="12" src="https://pure.md/favicon.png" alt="Pure.md Logo" /> **[Pure.md](https://github.com/puremd/puremd-mcp)** - Reliably access web content in markdown format with [pure.md](https://pure.md).
*   <img height="12" width="12" src="https://screenshotone.com/favicon.ico" alt="ScreenshotOne Logo" /> **[ScreenshotOne](https://github.com/screenshotone/mcp/)** - Render website screenshots with [ScreenshotOne](https://screenshotone.com/).
*   <img height="12" width="12" src="https://semgrep.dev/favicon.ico" alt="Semgrep Logo" /> **[Semgrep](https://github.com/semgrep/mcp)** - Enable AI agents to secure code with [Semgrep](https://semgrep.dev/).
*   <img height="12" width="12" src="https://tavily.com/favicon.ico" alt="Tavily Logo" /> **[Tavily](https://github.com/tavily-ai/tavily-mcp)** - Search engine for AI agents (search + extract) powered by [Tavily](https://tavily.com/).
*   <img height="12" width="12" src="https://raw.githubusercontent.com/hashicorp/terraform-mcp-server/main/public/images/Terraform-LogoMark_onDark.svg" alt="Terraform Logo" /> **[Terraform](https://github.com/hashicorp/terraform-mcp-server)** - Seamlessly integrate with Terraform ecosystem for IaC development powered by [Terraform](https://www.hashicorp.com/en/products/terraform).

This guide should serve as a good starting point for finding relevant MCP servers for our project needs. For a complete list and more details, always refer to the [modelcontextprotocol/servers GitHub repository](https://github.com/modelcontextprotocol/servers). 