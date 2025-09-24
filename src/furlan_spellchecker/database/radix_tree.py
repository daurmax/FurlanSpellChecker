"""Radix tree implementation for fast word lookups."""
from pathlib import Path
from typing import List, Optional, Iterator
import struct

from .interfaces import IRadixTree


class RadixTreeEdge:
    """An edge in the radix tree structure."""
    
    # Flag constants from COF implementation
    IS_WORD_FLAG = 128
    CASE_FLAG = 64
    IS_LEAF_FLAG = 32
    NO_FLAGS = ~(128 | 64 | 32)
    EDGE_HEAD_DIM = 1
    OFFSET_DIM = 4
    
    def __init__(self, offset: int, data: bytes):
        """Initialize edge at given offset in binary data."""
        self.offset = offset
        self.data = data
        self.flags = data[offset]
    
    def is_word(self) -> int:
        """Check if edge represents a complete word. Returns 0=no, 1=lowercase, 2=uppercase."""
        if self.flags & self.IS_WORD_FLAG:
            return 2 if (self.flags & self.CASE_FLAG) else 1
        return 0
    
    def is_lowercase(self) -> bool:
        """Check if word is lowercase only."""
        return not (self.flags & self.CASE_FLAG)
    
    def is_leaf(self) -> bool:
        """Check if this is a leaf edge (no child node)."""
        return bool(self.flags & self.IS_LEAF_FLAG)
    
    def get_string_length(self) -> int:
        """Get the length of the edge string."""
        return self.flags & self.NO_FLAGS
    
    def get_string(self) -> str:
        """Get the edge string."""
        start = self.offset + self.EDGE_HEAD_DIM
        length = self.get_string_length()
        try:
            return self.data[start:start + length].decode('iso-8859-1')
        except UnicodeDecodeError:
            # Fallback to latin-1 if iso-8859-1 fails
            return self.data[start:start + length].decode('latin-1', errors='ignore')
    
    def get_dimension(self) -> int:
        """Get total size of this edge in bytes."""
        return (self.EDGE_HEAD_DIM + self.get_string_length() + 
                (0 if self.is_leaf() else self.OFFSET_DIM))
    
    def get_child_node(self) -> Optional['RadixTreeNode']:
        """Get the child node if this is not a leaf."""
        if self.is_leaf():
            return None
        
        offset_pos = self.offset + self.EDGE_HEAD_DIM + self.get_string_length()
        node_offset = struct.unpack('<I', self.data[offset_pos:offset_pos + self.OFFSET_DIM])[0]
        child_offset = self.offset + node_offset
        
        if child_offset >= len(self.data):
            return None
            
        return RadixTreeNode(child_offset, self.data)


class RadixTreeNode:
    """A node in the radix tree structure."""
    
    NODE_HEAD_DIM = 1
    
    def __init__(self, offset: int, data: bytes):
        """Initialize node at given offset in binary data."""
        self.offset = offset
        self.data = data
        self.num_edges = data[offset] if offset < len(data) else 0
        self._next_edge_pos = offset + self.NODE_HEAD_DIM
        self._next_edge_num = 0
    
    def get_num_edges(self) -> int:
        """Get number of edges from this node."""
        return self.num_edges
    
    def get_edges(self) -> Iterator[RadixTreeEdge]:
        """Iterate over all edges from this node."""
        pos = self.offset + self.NODE_HEAD_DIM
        for _ in range(self.num_edges):
            if pos >= len(self.data):
                break
            edge = RadixTreeEdge(pos, self.data)
            yield edge
            pos += edge.get_dimension()
    
    def copy(self) -> 'RadixTreeNode':
        """Create a copy of this node."""
        return RadixTreeNode(self.offset, self.data)


class BinaryRadixTree(IRadixTree):
    """Binary radix tree implementation for fast word lookups."""
    
    NOLC_MARKER = '*'  # Marker for uppercase words from COF
    
    def __init__(self, file_path: Path):
        """Initialize radix tree from binary file."""
        self.file_path = file_path
        self._data: Optional[bytes] = None
        self._load_data()
    
    def _load_data(self) -> None:
        """Load binary data from file."""
        try:
            with open(self.file_path, 'rb') as f:
                self._data = f.read()
        except Exception as e:
            print(f"Error reading radix tree file: {e}")
            raise
    
    def get_root(self) -> RadixTreeNode:
        """Get the root node of the radix tree."""
        if not self._data:
            raise ValueError("RadixTree data not loaded")
        return RadixTreeNode(0, self._data)
    
    def has_word(self, word: str) -> bool:
        """Check if a word exists in the radix tree."""
        if not self._data:
            return False
        
        try:
            encoded_word = word.encode('iso-8859-1')
        except UnicodeEncodeError:
            return False
        
        return self._node_check(self.get_root(), encoded_word)
    
    def _node_check(self, node: RadixTreeNode, suffix: bytes) -> bool:
        """Check if suffix exists starting from given node."""
        for edge in node.get_edges():
            label = edge.get_string().encode('iso-8859-1')
            min_len = min(len(label), len(suffix))
            
            # Compare prefix
            if min_len == 0:
                continue
                
            comparison = 0
            for i in range(min_len):
                if label[i] < suffix[i]:
                    comparison = -1
                    break
                elif label[i] > suffix[i]:
                    comparison = 1
                    break
            
            if comparison == -1:
                continue
            elif comparison == 1:
                return False
            else:  # comparison == 0
                if len(label) > len(suffix):
                    return False
                elif len(label) == len(suffix):
                    return edge.is_word() > 0
                else:
                    if edge.is_leaf():
                        return False
                    else:
                        child_node = edge.get_child_node()
                        if child_node:
                            return self._node_check(child_node, suffix[len(label):])
                        return False
        
        return False
    
    def get_words_ed1(self, word: str) -> List[str]:
        """Get all words within edit distance 1 of the given word."""
        if not self._data:
            return []
        
        try:
            encoded_word = word.encode('iso-8859-1')
        except UnicodeEncodeError:
            return []
        
        suggestions = self._get_words(self.get_root(), encoded_word)
        
        # Decode suggestions back to strings
        result = []
        for suggestion in suggestions:
            try:
                decoded = suggestion.decode('iso-8859-1')
                result.append(decoded)
            except UnicodeDecodeError:
                continue
        
        return result
    
    def _edge_check(self, edge: RadixTreeEdge, suffix: bytes) -> int:
        """Check if suffix matches edge. Returns word type (0=no, 1=lowercase, 2=uppercase)."""
        label = edge.get_string().encode('iso-8859-1')
        min_len = min(len(label), len(suffix))
        
        # Compare prefix
        comparison = 0
        for i in range(min_len):
            if label[i] < suffix[i]:
                comparison = -1
                break
            elif label[i] > suffix[i]:
                comparison = 1
                break
        
        if comparison != 0:
            return 0
        
        if len(label) > len(suffix):
            return 0
        elif len(label) == len(suffix):
            return edge.is_word()
        else:
            if edge.is_leaf():
                return 0
            else:
                child_node = edge.get_child_node()
                if child_node:
                    return self._node_check(child_node, suffix[len(label):])
                return 0
    
    def _get_words(self, node: RadixTreeNode, word: bytes) -> List[bytes]:
        """Get all words within edit distance 1, following COF algorithm."""
        words = []
        
        for edge in node.get_edges():
            label_str = edge.get_string()
            label = label_str.encode('iso-8859-1')
            min_len = min(len(label), len(word))
            
            # Find first differing position
            i = 0
            while i < min_len and label[i] == word[i]:
                i += 1
            
            if i < min_len:
                # Characters differ at position i
                case_marker = b'*' if edge.is_word() == 2 else b''
                
                # Substitution: replace word[i] with label[i]
                tmp_word = word[:i] + label[i:i+1] + word[i+1:]
                case = self._edge_check(edge, tmp_word)
                if case:
                    marker = b'*' if case == 2 else b''
                    words.append(tmp_word + marker)
                
                # Insertion: insert label[i] before word[i]
                tmp_word = word[:i] + label[i:i+1] + word[i:]
                case = self._edge_check(edge, tmp_word)
                if case:
                    marker = b'*' if case == 2 else b''
                    words.append(tmp_word + marker)
                
                # Transposition and deletion (if next chars match)
                if (len(word) > i + 1 and 
                    len(label) > i and 
                    label[i] == word[i + 1]):
                    
                    # Deletion: remove word[i]
                    tmp_word = word[:i] + word[i+1:]
                    case = self._edge_check(edge, tmp_word)
                    if case:
                        marker = b'*' if case == 2 else b''
                        words.append(tmp_word + marker)
                    
                    # Transposition: swap word[i] and word[i+1]
                    if len(word) > i + 1:
                        tmp_word = (word[:i] + 
                                  word[i+1:i+2] + 
                                  word[i:i+1] + 
                                  word[i+2:])
                        case = self._edge_check(edge, tmp_word)
                        if case:
                            marker = b'*' if case == 2 else b''
                            words.append(tmp_word + marker)
            
            elif i < len(word):
                # label is prefix of word
                if not edge.is_leaf():
                    child_node = edge.get_child_node()
                    if child_node:
                        child_words = self._get_words(child_node, word[i:])
                        for child_word in child_words:
                            words.append(label + child_word)
                
                # Single character deletion at end
                if len(word) == i + 1:
                    case = edge.is_word()
                    if case:
                        marker = b'*' if case == 2 else b''
                        words.append(label + marker)
            
            elif i < len(label):
                # word is prefix of label
                # Single character insertion
                if len(label) == i + 1:
                    case = edge.is_word()
                    if case:
                        marker = b'*' if case == 2 else b''
                        words.append(label + marker)
            
            else:
                # Exact match on this part
                if not edge.is_leaf():
                    child_node = edge.get_child_node()
                    if child_node:
                        child_words = self._get_words(child_node, b'')
                        for child_word in child_words:
                            words.append(label + child_word)
        
        return words
    
    # IRadixTree interface methods
    def contains(self, word: str) -> bool:
        """Check if word exists in radix tree."""
        return self.has_word(word)
    
    def find_suggestions(self, word: str, max_suggestions: int = 10) -> List[str]:
        """Find spelling suggestions for a word."""
        suggestions = self.get_words_ed1(word)
        # Remove case markers and limit results
        clean_suggestions = []
        for suggestion in suggestions:
            clean_word = suggestion.rstrip('*')
            if clean_word not in clean_suggestions:
                clean_suggestions.append(clean_word)
        
        return clean_suggestions[:max_suggestions]
    
    def get_words_with_prefix(self, prefix: str, max_results: int = 100) -> List[str]:
        """Get words starting with given prefix."""
        # This would require traversing to the prefix node and collecting all words
        # For now, return empty list as this is not needed for current COF compatibility
        return []
    
    def get_root(self) -> RadixTreeNode:
        """Get the root node of the tree."""
        if not self._data:
            raise RuntimeError("Radix tree data not loaded")
        return RadixTreeNode(0, self._data)
    
    def contains(self, word: str) -> bool:
        """Check if word exists in radix tree."""
        if not self._data or not word:
            return False
        
        # TODO: Implement binary search based on the actual format
        # For now, this is a placeholder implementation
        # The actual implementation would need to traverse the tree structure
        return self._search_word(word.lower())
    
    def find_suggestions(self, word: str, max_suggestions: int = 10) -> List[str]:
        """Find spelling suggestions for a word."""
        if not self._data or not word:
            return []
        
        # TODO: Implement suggestion algorithm
        # This would typically involve:
        # 1. Finding closest matches in the tree
        # 2. Computing edit distance
        # 3. Returning best matches
        return []
    
    def get_words_with_prefix(self, prefix: str, max_results: int = 100) -> List[str]:
        """Get words starting with given prefix."""
        if not self._data or not prefix:
            return []
        
        # TODO: Implement prefix search
        # This would involve:
        # 1. Navigating to the prefix node
        # 2. Collecting all terminal nodes in the subtree
        return []
    
    def _search_word(self, word: str) -> bool:
        """Internal method to search for a word in the tree."""
        # TODO: Implement actual binary tree traversal
        # This is a placeholder that would need to be implemented
        # based on the specific binary format used by the C# version
        
        # The C# version uses a binary format where the tree structure
        # is serialized. We would need to understand that format to
        # properly implement this.
        return False
    
    def print_first_n_bytes(self, n: int) -> None:
        """Print first n bytes of binary data for debugging."""
        if not self._data or n <= 0:
            return
        
        bytes_to_print = min(n, len(self._data))
        hex_values = [f"{self._data[i]:02X}" for i in range(bytes_to_print)]
        print("-".join(hex_values))
    
    def print_total_bytes(self) -> None:
        """Print total number of bytes in the data."""
        if self._data:
            print(f"Total number of bytes: {len(self._data)}")
        else:
            print("No data loaded")


class RadixTreeDatabase:
    """High-level interface for radix tree operations."""
    
    def __init__(self, radix_tree_path):
        """Initialize with path to radix tree file."""
        self.radix_tree_path = Path(radix_tree_path) if isinstance(radix_tree_path, str) else radix_tree_path
        self._tree: Optional[BinaryRadixTree] = None
    
    def _ensure_loaded(self) -> BinaryRadixTree:
        """Ensure radix tree is loaded."""
        if self._tree is None:
            if not self.radix_tree_path.exists():
                raise FileNotFoundError(f"Radix tree file not found at '{self.radix_tree_path}'")
            self._tree = BinaryRadixTree(self.radix_tree_path)
        return self._tree
    
    def has_word(self, word: str) -> bool:
        """Check if word exists in radix tree."""
        tree = self._ensure_loaded()
        return tree.has_word(word)
    
    def get_words_ed1(self, word: str) -> List[str]:
        """Get all words within edit distance 1 of the given word."""
        tree = self._ensure_loaded()
        return tree.get_words_ed1(word)
    
    def contains_word(self, word: str) -> bool:
        """Check if word exists in radix tree."""
        tree = self._ensure_loaded()
        return tree.has_word(word)
    
    def get_suggestions(self, word: str, max_suggestions: int = 10) -> List[str]:
        """Get spelling suggestions for a word."""
        tree = self._ensure_loaded()
        return tree.get_words_ed1(word)[:max_suggestions]
    
    def get_completions(self, prefix: str, max_results: int = 100) -> List[str]:
        """Get word completions for a prefix.""" 
        tree = self._ensure_loaded()
        return tree.get_words_ed1(prefix)[:max_results]