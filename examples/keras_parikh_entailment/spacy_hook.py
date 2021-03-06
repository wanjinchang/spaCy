from keras.models import model_from_json


class KerasSimilarityShim(object):
    @classmethod
    def load(cls, path, nlp, get_features=None):
        if get_features is None:
            get_features = doc2ids
        with (path / 'config.json').open() as file_:
            config = json.load(file_)
        model = model_from_json(config['model'])
        with (path / 'model').open('rb') as file_:
            weights = pickle.load(file_)
        embeddings = get_embeddings(nlp.vocab)
        model.set_weights([embeddings] + weights)
        return cls(model, get_features=get_features)

    def __init__(self, model, get_features=None):
        self.model = model
        self.get_features = get_features

    def __call__(self, doc):
        doc.user_hooks['similarity'] = self.predict
        doc.user_span_hooks['similarity'] = self.predict
    
    def predict(self, doc1, doc2):
        x1 = self.get_features(doc1)
        x2 = self.get_features(doc2)
        scores = self.model.predict([x1, x2])
        return scores[0]


def get_embeddings(cls, vocab):
    max_rank = max(lex.rank+1 for lex in vocab if lex.has_vector)
    vectors = numpy.ndarray((max_rank+1, vocab.vectors_length), dtype='float32')
    for lex in vocab:
        if lex.has_vector:
            vectors[lex.rank + 1] = lex.vector
    return vectors


def get_word_ids(docs, max_length=100):
    Xs = numpy.zeros((len(docs), max_length), dtype='int32')
    for i, doc in enumerate(docs):
        j = 0
        for token in doc:
            if token.has_vector and not token.is_punct and not token.is_space:
                Xs[i, j] = token.rank + 1
                j += 1
                if j >= max_length:
                    break
    return Xs


def create_similarity_pipeline(nlp):
    return [SimilarityModel.load(
                nlp.path / 'similarity',
                nlp,
                feature_extracter=get_features)]



