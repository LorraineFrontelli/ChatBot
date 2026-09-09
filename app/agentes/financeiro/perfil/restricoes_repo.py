"""Perfil financeiro — parte em texto livre (`restricoes`), indexada no
Qdrant para busca semântica.

Cada restrição vira um PONTO PRÓPRIO (não um vetor da lista inteira): se as
3 frases fossem embeddadas juntas como um bloco só, a busca por similaridade
pesaria o bloco inteiro, e a frase que não for o tema dominante perde força
— a terceira restrição "some" da busca mesmo estando lá. Um ponto por
restrição faz cada frase competir individualmente pela pergunta do usuário.

Diferente de "faq_chunks"/"memoria_resumos" (provisionadas fora deste
código), "perfil_restricoes" é criada por aqui mesmo, de forma idempotente —
não há outro lugar no projeto que a provisione.
"""
import uuid

from qdrant_client import models

from app.vectorstore import (
    COLLECTION_PERFIL_RESTRICOES,
    EMBEDDING_DIM,
    gerar_embedding,
    gerar_embeddings_batch,
    qdrant,
)


def _garantir_collection() -> None:
    if not qdrant.collection_exists(COLLECTION_PERFIL_RESTRICOES):
        qdrant.create_collection(
            collection_name=COLLECTION_PERFIL_RESTRICOES,
            vectors_config=models.VectorParams(size=EMBEDDING_DIM, distance=models.Distance.COSINE),
        )
    # Índice de payload em user_id: sem ele o Qdrant (nesta instância)
    # recusa filtrar/apagar por esse campo — e é esse filtro que isola as
    # restrições de um usuário das de outro. Chamada idempotente (mesmo
    # espírito do create_index dos repositórios Mongo), pra cobrir também
    # uma collection que já existisse sem o índice.
    qdrant.create_payload_index(
        collection_name=COLLECTION_PERFIL_RESTRICOES,
        field_name="user_id",
        field_schema=models.PayloadSchemaType.KEYWORD,
    )


def salvar_restricoes(user_id: str, restricoes: list[str]) -> None:
    """Substitui TODAS as restrições deste usuário pelas informadas: apaga
    primeiro (por user_id, não a collection inteira) e só depois insere as
    novas — sem isso, restrições removidas em um novo salvamento continuariam
    aparecendo na busca para sempre."""
    _garantir_collection()

    qdrant.delete(
        collection_name=COLLECTION_PERFIL_RESTRICOES,
        points_selector=models.FilterSelector(
            filter=models.Filter(
                must=[models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id))]
            )
        ),
    )

    if not restricoes:
        return

    vetores = gerar_embeddings_batch(restricoes)
    pontos = [
        models.PointStruct(
            id=str(uuid.uuid4()),
            vector=vetor,
            payload={"user_id": user_id, "texto": texto},
        )
        for vetor, texto in zip(vetores, restricoes)
    ]
    qdrant.upsert(collection_name=COLLECTION_PERFIL_RESTRICOES, points=pontos)


def buscar_restricoes_relevantes(user_id: str, pergunta: str, limite: int = 3) -> list[str]:
    """Restrições deste usuário mais relevantes semanticamente para `pergunta`
    — não é busca por palavra: uma pergunta sobre "deixar o dinheiro travado"
    encontra uma restrição que só fala em "guardar pra consertar o carro",
    sem nenhuma palavra em comum entre as duas.

    O filtro por user_id é obrigatório: sem ele a busca vetorial poderia
    devolver a restrição de outro usuário só por parecer semanticamente
    parecida com a pergunta."""
    if not qdrant.collection_exists(COLLECTION_PERFIL_RESTRICOES):
        return []

    vetor = gerar_embedding(pergunta)
    resultados = qdrant.query_points(
        collection_name=COLLECTION_PERFIL_RESTRICOES,
        query=vetor,
        query_filter=models.Filter(
            must=[models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id))]
        ),
        limit=limite,
    )
    return [ponto.payload["texto"] for ponto in resultados.points]
