# mutations retiradas da doc do pipefy
# https://developers.pipefy.com/reference/createcard
# https://developers.pipefy.com/reference/updatecardfield

CREATE_CARD_MUTATION = """
mutation CreateCard($input: CreateCardInput!) {
  createCard(input: $input) {
    card {
      id
      title
      created_at
    }
  }
}
"""

UPDATE_CARD_FIELD_MUTATION = """
mutation UpdateCardField($input: UpdateCardFieldInput!) {
  updateCardField(input: $input) {
    card {
      id
    }
    success
  }
}
"""
