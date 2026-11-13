from models.Trie import Trie

trie = Trie()
trie.insertar("kenan", "id1")
trie.insertar("kevin", "id2")
trie.insertar("ken", "id3")
trie.insertar("ana", "id4")
trie.insertar("José", "id5")

print(trie.buscar_prefijo("ke"))    # id3, id1, id2
print(trie.buscar_prefijo("ken"))   # id3, id1
print(trie.buscar_prefijo("jose"))  # id5 (sin tilde)
print(trie.buscar_prefijo("zz"))    # []
print("Nodos:", trie.total_nodos)