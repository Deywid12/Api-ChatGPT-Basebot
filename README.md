O **BaseBot** é uma **API de suporte técnico** desenvolvida para a **Radio Memory**, com o objetivo de centralizar a base de conhecimento de **erros, manutenções e integrações** dos sistemas **Studio** e **XWork**.
Toda a base de dados é fornecida ao GPT em formato de **texto estruturado**, permitindo que ele responda de forma precisa e consistente.

# BaseBot (Flask + RAG)
## 🚀 Funcionalidades

* Estrutura organizada com **Causa, Tratativa e Observações**
* Base de conhecimento documentada em texto no GPT
* API pronta para consultas de suporte
* Foco em erros, manutenções e integrações

## 📂 Estrutura do Projeto

```
📦 basebot
 ┣ 📂 data                # banco de dados
 ┣ 📜 .env.example        # aqruivo env
 ┣ 📜 license             # Licença de uso
 ┣ 📜 README.md           # Documentação do projeto
 ┗ 📜 openai_client.py    # Link da key do GPT
 ┣ 📜 rag.py              # Configurações da API
 ┣ 📜 requirements.txt    # Arquivos necessarios para rodar a API
 ┗ 📜 schema.py           # Aquivo schema
````

## Testes rápidos
```bash
curl -s http://localhost:8000/health
curl -s "http://localhost:8000/search?q=twain&classe=erros&k=5"
curl -sX POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{"query":"Erro: Error starting TCP/UDP receive thread", "classe":"erros"}' | jq
```


## 👨‍💻 Autores

**Deywid Souza**
💼 Técnico de Suporte na [Radio Memory](https://www.radiomemory.com.br/)
🎓 Ciência da computação - UNA
🚀 **IA, automação e backend**

[![LinkedIn](https://img.shields.io/badge/-Deywid_Souza-0077B5?style=for-the-badge\&logo=linkedin\&logoColor=white)](https://www.linkedin.com/in/deywid-souza/)
[![GitHub](https://img.shields.io/badge/-Deywid12-181717?style=for-the-badge\&logo=github\&logoColor=white)](https://github.com/Deywid12)


**Victor Raphael**
💼 Técnico de Suporte na [Radio Memory](https://www.radiomemory.com.br/)
🎓 Engenharia de Software - UNA
🚀 Entusiasta de **IA, automação e backend**

[![LinkedIn](https://img.shields.io/badge/-Victor_Raphael-0077B5?style=for-the-badge\&logo=linkedin\&logoColor=white)](https://www.linkedin.com/in/dev-victor-raphael)
[![GitHub](https://img.shields.io/badge/-EooVictor-181717?style=for-the-badge\&logo=github\&logoColor=white)](https://github.com/EooVictor)



