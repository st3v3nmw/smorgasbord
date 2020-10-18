#include <iostream>
#include <fstream>
#include <memory>
#include <map>
#include <cstdlib>
#include <cstring>
#include <sys/wait.h>
#include <signal.h>
#include <unistd.h>

#define IDENT_LIM 256 // limit on identifier length
#define IDENT_BUFFER_LEN IDENT_LIM + 1
#define NOREG -1
#define NOSEGINT -1

using namespace std;

// list of printable tokens
string tokstr[] = {
    "eof",
    "+", "-", "*", "/",
    "==", "!=", "<", ">", "<=", ">=",
    "intlit", ";", "=", "identifier",
    "{", "}", "(", ")",
    "print", "int", "if", "else", "while"
};

// Tokens
enum {
  T_EOF,
  T_PLUS, T_MINUS,  // additive operators
  T_STAR, T_SLASH,  // multiplicative operators
  T_EQ, T_NEQ,       // ==, !=
  T_LT, T_GT, T_LE, T_GE, // <, >, <=, >=
  T_INTLIT, T_SEMI, T_ASSIGN, T_IDENT,
  T_LBRACE, T_RBRACE, T_LPAREN, T_RPAREN,
  T_PRINT, T_INT, T_IF, T_ELSE, T_WHILE, T_FOR, T_VOID, T_CHAR // keywords
};

// operator precedence for each token
static int opPrec[] = {
    0, 1, 1,    // T_EOF, T_PLUS, T_MINUS
    2, 2,       // T_STAR, T_SLASH
    3, 3,       // T_EQ, T_NEQ
    4, 4, 4, 4  // T_LT, T_GT, T_LE, T_GE
};

class Token {
    public:
        Token() {}
    
    private:
        int token, value;
    friend class Compiler;
};

// AST node types
enum {
  A_ADD = 1, A_SUBTRACT, A_MULTIPLY, A_DIVIDE,
  A_EQ, A_NEQ, A_LT, A_GT, A_LE, A_GE,
  A_INTLIT,
  A_IDENT, A_LVIDENT, A_ASSIGN,
  A_PRINT, A_GLUE, A_IF, A_WHILE, A_FUNCTION, A_WIDEN
};

// Abstract Syntax Tree node
class ASTNode {
    public:
        ASTNode(int op, int value) { // node without subtrees
            init(op, value);
            left = NULL;
            right = NULL;
        }

        ASTNode(int op, int value, shared_ptr<ASTNode> left_node, shared_ptr<ASTNode> right_node) {
            init(op, value);
            left = left_node;
            right = right_node;
        }

        ASTNode(int op, int value, shared_ptr<ASTNode> left_node, shared_ptr<ASTNode> mid_node, shared_ptr<ASTNode> right_node) {
            init(op, value);
            left = left_node;
            mid = mid_node;
            right = right_node;
        }

        ASTNode(int op, int value, int type, shared_ptr<ASTNode> left_node) { // unary
            init(op, value);
            left = left_node;
        }

        ASTNode(int op, int value, int type) {
            init(op, value);
            ASTNode::type = type;
        }

        void traverse() {
            // print in preorder (prefix notation)
            if (op == A_INTLIT)
                cout << value << " ";
            else
                cout << tokstr[op] << " ";

            if (left)
                left->traverse();
                
            if (right)
                right->traverse();
        }

    private:
        int op; // operation to be performed
        int value; // For A_INTLIT's integer value or for A_IDENT the symbol slot
        int type; // type of any expression this tree generates
        shared_ptr<ASTNode> left, mid, right; // these f[a-z]*ing pointers :(

        inline void init(int op, int value) {
            ASTNode::op = op;
            ASTNode::value = value;
        }

    friend class Compiler;
};


// Primitive types
enum {
    P_NONE, P_VOID, P_CHAR, P_INT
};

// structural types

enum {
    S_VARIABLE, S_FUNCTION
};


class SymTableStructure {
    public:
        SymTableStructure() {}

        SymTableStructure(string name, int type, int stype) {
            SymTableStructure::name = name;
            SymTableStructure::type = type;
            SymTableStructure::stype = stype;
        }
    
    private:
        string name;
        int type; // primitive type for the symbol
        int stype; // structural type for the symbol
    friend class Compiler;
};

// handle segmentation faults and other error exits
void handler(int sig) {
    // print the backtrace using gdb
    char pid_buf[32];
    sprintf(pid_buf, "%d", getpid());
    char name_buf[512];
    name_buf[readlink("/proc/self/exe", name_buf, 511)] = 0;

    int child_pid = fork();
    if (!child_pid) {
        dup2(2, 1); // redirect output to stderr
        fprintf(stdout, "\nStack trace for %s pid=%s\n", name_buf, pid_buf);
        execlp("gdb", "gdb", "--batch", "-n", "-ex", "thread", "-ex", "bt", name_buf, pid_buf, NULL);
        abort(); // if gdb failed to start
    } else {
        waitpid(child_pid, NULL, 0);
    }

    exit(1);
}

class Compiler {
    public:
        Compiler(string path) {
            // read file
            inputPath = path;
            ifstream inputFl(path, ios::in);
            if (!inputFl) {
                cerr << "Unable to open " << path << endl;
                exit(1);
            }
            inputFile.swap(inputFl);

            // get the cleaned up filename
            int name_start = path.find_last_of('/');
            int name_end = path.find_last_of('.');
            filename = path.substr(name_start != -1 ? name_start + 1: 0, name_end != -1 ? name_end : path.length());

            // assembly output file
            outputPath = "./out/" + filename + ".s";
            ofstream outputFl(outputPath, ios::out);
            if (!outputFl) {
                cerr << "Couldn't create out file" << endl;
                exit(1);
            }
            outputFile.swap(outputFl);

            // output preamble
            cg_preamble();

            // parse and generate assembly code
            scanChars(); // get the 1st token
            while (1) {
                root = function_declaration(); // parse the statements
                genASM(root, NOREG, 0);
                if (t.token == T_EOF)
                    break;
            }
            
            cout << filename << " parsed successfully :)" << endl;
        }


        /* scanning and parsing */
    
        shared_ptr<ASTNode> compound_statement() {
            shared_ptr<ASTNode> left = NULL, tree;

            match(T_LBRACE, "{");

            while (1) {
                    tree = single_statement();

                    if (tree != NULL && (tree->op == A_PRINT || tree->op == A_ASSIGN))
                        match(T_SEMI, ";");
                    
                    // for each new tree, either save it in left if it's empty, or glue the left and the new tree together
                    if (tree) {
                        if (left == NULL)
                            left = tree;
                        else {
                            shared_ptr<ASTNode> left2(new ASTNode(A_GLUE, 0, left, NULL, tree));
                            left = left2;
                        }
                    }
                    
                    // when we hit a }, we skip past it and return the AST
                    if (t.token == T_RBRACE) {
                        match(T_RBRACE, "}");
                        return left;
                    }
            }
        }

        // single statement without scanning ending semicolon i.e. for for loop
        shared_ptr<ASTNode> single_statement() {
            switch(t.token) {
                case T_PRINT:   return print_statement();
                case T_CHAR:
                case T_INT:
                    var_declaration();
                    return NULL; // no AST generated
                case T_IDENT:   return assignment_statement();
                case T_IF:      return if_statement();
                case T_WHILE:   return while_statement();
                case T_FOR:     return for_statement();
                default:
                    error_exit("Syntax error, token", tokstr[t.token]);
                    exit(1); // unreachable
            }
        }

        // handle a print statement
        shared_ptr<ASTNode> print_statement() {
            shared_ptr<ASTNode> node;
            int reg;
            // match a 'print' as the first token
            match(T_PRINT, "print");

            // parse the expression & generate the assembly code
            node = binexpr(0);

            int leftType = P_INT;
            int rightType = node->type;
            if (!type_compatible(&leftType, &rightType, 0))
                error_exit("Incompatible types", "");
            
            // widen the tree if required
            if (rightType) {
                shared_ptr<ASTNode> n(new ASTNode(A_PRINT, 0, P_INT, node));
                node = n;
            }

            shared_ptr<ASTNode> node2(new ASTNode(A_PRINT, 0, 0, node));
            return node2;
        }

        // handle a declaration statement
        void var_declaration() {
            // data type then identifier then semicolon
            int type = parse_type(t.token);
            scanChars();
            match(T_IDENT, "identifier");
            int id = addglob(string(buf), type, S_VARIABLE);
            cg_globsym(id);
            match(T_SEMI, ";");
        }

        // handle an assignment statement
        shared_ptr<ASTNode> assignment_statement() {
            shared_ptr<ASTNode> left;

            // ensure we have an identifier
            match(T_IDENT, "identifier");

            // check if it's been defined then make a leaf node for it
            string name(buf);
            int id = findglob(name);
            if (id == -1)
                error_exit("Undeclared variable", name);

            shared_ptr<ASTNode> right(new ASTNode(A_LVIDENT, id));

            // ensure we have an assignment operator
            match(T_ASSIGN, "=");

            // parse the following expressino
            left = binexpr(0);

            // make an assignment AST tree
            shared_ptr<ASTNode> tree(new ASTNode(A_ASSIGN, 0, left, NULL, right));
            return tree;
        }

        shared_ptr<ASTNode> if_statement() {
            shared_ptr<ASTNode> condAST, trueAST, falseAST = NULL;

            // ensure we have 'if' '('
            match(T_IF, "if");
            match(T_LPAREN, "(");

            // parse the following expression and the ')' following.
            // Ensure the tree's op is a comparison.
            condAST = binexpr(0);

            if (condAST->op < A_EQ || condAST->op > A_GE)
                error_exit("Bad comparison operator", condAST->op);
            match(T_RPAREN, ")");
            
            // get the AST for the compound statement
            trueAST = compound_statement();

            // If we have an 'else', skip it
            // and get the AST for the compound statement
            if (t.token == T_ELSE) {
                scanChars();
                falseAST = compound_statement();
            }

            // build and return the AST
            shared_ptr<ASTNode> r(new ASTNode(A_IF, 0, condAST, trueAST, falseAST));
            return r;
        }

        shared_ptr<ASTNode> while_statement() {
            shared_ptr<ASTNode> condAST, bodyAST;

            match(T_WHILE, "while");
            match(T_LPAREN, "(");

            condAST = binexpr(0);
            if (condAST->op < A_EQ || condAST->op > A_GE)
                error_exit("Bad comparison operator", "");
            match(T_RPAREN, ")");

            bodyAST = compound_statement();

            shared_ptr<ASTNode> r(new ASTNode(A_WHILE, 0, condAST, NULL, bodyAST));
            return r;
        }

        shared_ptr<ASTNode> for_statement() {
            shared_ptr<ASTNode> condAST, bodyAST, preopAST, postopAST;

            match(T_FOR, "for");
            match(T_LPAREN, "(");

            preopAST = single_statement();
            match(T_SEMI, ";");

            condAST = binexpr(0);
            if (condAST->op < A_EQ || condAST->op > A_GE)
                error_exit("Bad comparison operator", "");
            match(T_SEMI, ";");

            postopAST = single_statement();
            match(T_RPAREN, ")");

            bodyAST = compound_statement();

            shared_ptr<ASTNode> tree1(new ASTNode(A_GLUE, 0, bodyAST, NULL, postopAST));
            shared_ptr<ASTNode> tree2(new ASTNode(A_WHILE, 0, condAST, NULL, tree1));
            shared_ptr<ASTNode> tree(new ASTNode(A_GLUE, 0, preopAST, NULL, tree2));
            return tree;
        }

        shared_ptr<ASTNode> function_declaration() {
            shared_ptr<ASTNode> tree;

            match(T_VOID, "void");
            match(T_IDENT, "identifier");
            int nameslot = addglob(string(buf), P_VOID, S_FUNCTION);
            match(T_LPAREN, "(");
            match(T_RPAREN, ")");

            tree = compound_statement();
            shared_ptr<ASTNode> tree2(new ASTNode(A_FUNCTION, nameslot, 0, tree));
            return tree2;
        }

        // ensure that the current token is t and fetch the next token
        // else throw an error
        void match(int t2, string what) {
            if (t.token== t2) {
                scanChars();
            } else {
                error_exit(what, "expected on line");
            }
        }

        // return an AST tree whose root is a binary operator
        // Parameter ptp is the previous token's precedence
        shared_ptr<ASTNode> binexpr(int ptp) {
            shared_ptr<ASTNode> left, right;
            left = primary(); // build the left sub-tree

            int tokenType = t.token, leftType, rightType;
            if (tokenType == T_SEMI || tokenType == T_RPAREN) // statements terminated by a semicolon
                return left;
        
            // while the precedence of this token
            // is more than that of the previous token precedence
            while (opPrecedence(tokenType) > ptp) {
                scanChars();

                // recursively call parse with the precedence
                // of our token to build a sub-tree
                right = binexpr(opPrec[tokenType]);

                // Ensure the two types are compatible
                leftType = left->type;
                rightType = right->type;
                if (!type_compatible(&leftType, &rightType, 0))
                    error_exit("Incompatible types", "");

                // widen either side if required. type vars are A_WIDEN now
                if (leftType) {
                    shared_ptr<ASTNode> left2(new ASTNode(leftType, 0, right->type, left));
                    left = left2;
                }
                if (rightType) {
                    shared_ptr<ASTNode> right2(new ASTNode(rightType, 0, left->type, right));
                    right = right2;
                }

                // join the right sub-tree above with the tree we already have
                shared_ptr<ASTNode> left2(new ASTNode(tokenToASTOp(tokenType), 0, left, right));
                left = left2;

                tokenType = t.token;
                if (tokenType == T_SEMI || tokenType == T_RPAREN)
                    break;
            }

            return left;
        }

        // return a node with a number (T_INTLIT)
        shared_ptr<ASTNode> primary() {
            switch (t.token) {
                case T_INTLIT:
                    {
                        shared_ptr<ASTNode> node;
                        if (t.value >= 0 && t.token < 256) {
                            shared_ptr<ASTNode> node2(new ASTNode(A_INTLIT, t.value, P_CHAR));
                            node = node2;
                        }
                        else {
                            shared_ptr<ASTNode> node2(new ASTNode(A_INTLIT, t.value, P_INT));
                            node = node2;
                        }
                        scanChars();
                        return node; 
                    }
                case T_IDENT:
                    {
                        // check that this identifier exists
                        string name(buf);
                        int id = findglob(name);
                        if (id == -1)
                            error_exit("Unknown variable", name);

                        shared_ptr<ASTNode> node(new ASTNode(A_IDENT, id, Gsym[id].type));
                        scanChars();
                        return node;
                    }
                default:
                    error_exit("Syntax error", "");
                    exit(1); // unreachable
            }
        }

        int scanChars() {
            if (!skip()) { // read the next character, skip whitespace
                t.token = T_EOF;
                return 0; //EOF
            }

            switch (c) { // determine token type
                case '+':
                    t.token = T_PLUS;
                    break;
                case '-':
                    t.token = T_MINUS;
                    break;
                case '*':
                    t.token = T_STAR;
                    break;
                case '/':
                    t.token = T_SLASH;
                    break;
                case ';':
                    t.token = T_SEMI;
                    break;
                case '{':
                    t.token = T_LBRACE;
                    break;
                case '}':
                    t.token = T_RBRACE;
                    break;
                case '(':
                    t.token = T_LPAREN;
                    break;
                case ')':
                    t.token = T_RPAREN;
                    break;
                case '=':
                    next();
                    if (c == '=') // ==
                        t.token = T_EQ;
                    else {
                        inputFile.putback(c);
                        t.token = T_ASSIGN;
                    }
                    break;
                case '!':
                    next();
                    if (c == '=')
                        t.token = T_NEQ;
                    else
                        error_exit("Unrecognized character", c);
                    break;
                case '<':
                    next();
                    if (c == '=')
                        t.token = T_LE;
                    else {
                        inputFile.putback(c);
                        t.token = T_LT;
                    }
                    break;
                case '>':
                    next();
                    if (c == '=')
                        t.token = T_GE;
                    else {
                        inputFile.putback(c);
                        t.token = T_GT;
                    }
                    break;
                default:
                    if (isdigit(c)) {
                        t.value = scanint(); // if it's a digit, scan the literal integer value
                        t.token = T_INTLIT;
                        break;
                    } else if (isalpha(c) || '_' == c) {
                        // scan keyword or identifier
                        scanident();

                        // if it's a recognized keyword, return token
                        int tokenType = keyword();
                        if (tokenType) {
                            t.token = tokenType;
                            break;
                        }

                        // not a recognized keyword, so it must be an identifier
                        t.token = T_IDENT;
                        break;
                    }

                    error_exit("Unrecognized character", c);
            }
            return 1; // we found a token
        }

        // scan an integer
        int scanint() {
            int val = 0;
            while(isdigit(c)) {
                val = val * 10 + c - 48; // offset by 48 to convert ASCII to integer
                next();
            }

            inputFile.putback(c); // put back a non-int character
            line_pos--; // decrement our line position when we put back a character
            return val;
        }

        // scan an identifier
        int scanident() {
            int i = 0;
            // allow alphanumeric & underscores
            while (isalnum(c) || '_' == c) {
                // error if we reach the identifier length limit,
                // else append to buf and get next char
                if (ident_lim - 1 == i)
                    error_exit("Identifier too long on", "");
                buf[i++] = c;
                next();
            }

            buf[i] = '\0'; // null terminate buf
            // put back a non-valid char
            inputFile.putback(c);
            line_pos--;
            return i; // length of identifier
        }

        // given a word in the buffer buf, return the matching keyword
        // token number or 0 if it's not a keyword
        int keyword() {
            switch(buf[0]) {
                case 'c':
                    if (!strcmp(buf, "char"))   return T_CHAR;
                case 'e':
                    if (!strcmp(buf, "else"))   return T_ELSE;
                case 'f':
                    if (!strcmp(buf, "for"))    return T_FOR;
                case 'i':
                    if (!strcmp(buf, "if"))     return T_IF;
                    if (!strcmp(buf, "int"))    return T_INT;
                case 'p':
                    if (!strcmp(buf, "print"))  return T_PRINT;
                case 'v':
                    if (!strcmp(buf, "void"))   return T_VOID;
                case 'w':
                    if (!strcmp(buf, "while"))  return T_WHILE;
            }
            return 0;
        }

        // parse the current token and return a primitive type enum value
        int parse_type(int t2) {
            if (t2 == T_CHAR)   return P_CHAR;
            if (t2 == T_INT)    return P_INT;
            if (t2 == T_VOID)   return P_VOID;
            error_exit("Illegal type, token", t2);
            return -1; // unreachable code
        }

        // given two primitive types, return true if they're compatible
        // false otherwise. Also return either zero or an A_WIDEN
        // operation if one has to be widened to match the other.
        // If onlyright is true, only widen left to right.
        int type_compatible(int *left, int *right, int onlyright) {
            // voids not compatible with anything
            if (*left == P_VOID || *right == P_VOID)  return 0;

            // same types compatible
            if (*left == *right) {
                *left = *right = 0;
                return 1;
            }

            // widen P_CHARS to P_INTs as required
            if (*left == P_CHAR && *right == P_INT) {
                *left = A_WIDEN;
                *right = 0;
                return 1;
            }
            if (*left == P_INT && *right == P_CHAR) {
                if (onlyright) return 0;
                *left = 0;
                *right = A_WIDEN;
                return 1;
            }

            // anything remaining is compatible, for now
            *left = *right = 0;
            return 1;
        }

        // get the next character
        int next() {
            if (!(inputFile >> noskipws >> c))
                    return 0; // EOF
            if (c == '\n') {
                n_line++;
                line_pos = 0; // reset out position on the line
            }

            line_pos++; // increment our position on the current line
            return 1; // we found a char
        }

        // skip whitespace
        int skip() {
            c = ' ';
            while (' ' == c || '\t' == c || '\n' == c || '\r' == c || '\f' == c) {
                if(!next())
                    return 0; // EOF
            }
            return 1;
        }

        // convert a token into an AST operation
        // 1:1 mapping
        int tokenToASTOp(int tokenType) {
            if (tokenType > T_EOF && tokenType < T_INTLIT)
                return tokenType;
            error_exit("Unknown token", tokstr[tokenType]);
            return -1; // unreachable code
        }

        // return a tokenType's precedence
        int opPrecedence(int tokenType) {
            int prec = opPrec[tokenType];
            if (prec == 0) {
                error_exit("Syntax error, token", tokstr[tokenType]);
            }
            return prec;
        }


        /* code generation */

        // given an AST, generate assembly code recursively
        // the register (if any) holds the previous rvalue
        // parentASTop holds the parent's operation
        int genASM(shared_ptr<ASTNode> node, int reg, int parentASTop) {
            // int leftval = 0, rightval = 0;
            int leftreg, rightreg;

            // specific AST node handling
            switch (node->op) {
                case A_IF:
                    return genIfASM(node);
                case A_WHILE:
                    return genWhile(node);
                case A_GLUE:
                    // do each child statement, & free the registers after each child
                    genASM(node->left, NOREG, node->op);
                    free_all_registers();
                    genASM(node->right, NOREG, node->op);
                    free_all_registers();
                    return NOREG;
                case A_FUNCTION:
                    cg_func_preamble(Gsym[node->value].name);
                    genASM(node->left, NOREG, node->op);
                    cg_func_postamble();
                    return NOREG;
            }

            // general AST node handling

            // get the values of the left and right subtrees
            if (node->left)  leftreg  = genASM(node->left, NOREG, node->op);
            if (node->right) rightreg = genASM(node->right, leftreg, node->op);

            switch (node->op) {
                case A_ADD:      return cg_add(leftreg, rightreg);
                case A_SUBTRACT: return cg_sub(leftreg, rightreg);
                case A_MULTIPLY: return cg_mul(leftreg, rightreg);
                case A_DIVIDE:   return cg_div(leftreg, rightreg);
                case A_INTLIT:   return cg_load(node->value);
                case A_IDENT:    return cg_load_glob(node->value);
                case A_LVIDENT:  return cg_store_glob(reg, node->value);
                case A_ASSIGN:   return rightreg; // the work has already been done
                case A_WIDEN:    return cg_widen(leftreg, node->left->type, node->type);
                case A_EQ:
                case A_NEQ:
                case A_LT:
                case A_GT:
                case A_LE:
                case A_GE:
                    // if the parent AST node is an A_IF or a A_WHILE, generate a compare followed by a jump. Otherwise, compare registers and set 1 or 0 based on the comparison.
                    if (parentASTop == A_IF || parentASTop == A_WHILE)
                        return cg_compare_and_jump(node->op, leftreg, rightreg, reg);
                    else
                        return cg_compare_and_set(node->op, leftreg, rightreg);
                case A_PRINT:
                    // print the left child's value
                    cg_printint(leftreg);
                    free_all_registers();
                    return NOREG;
                default:
                    error_exit("Unknown AST operator", node->op);
                    exit(1);
            }
        }

        int genIfASM(shared_ptr<ASTNode> node) {
            int lFalse, lEnd;

            // create two labels
            // one for the false compound statement
            // another for the end of the overall IF statement
            // if there's no else clause, lFalse is the ending label.
            lFalse = label_id++;
            if (node->right)
                lEnd = label_id++;

            // generate the condition code followed by a zero jump to the false label.
            genASM(node->left, lFalse, node->op);
            free_all_registers();

            // generate the true compound statement
            genASM(node->mid, NOREG, node->op);
            free_all_registers();

            // if there is an optional ELSE clause
            // generate the jump to skip to the end
            if (node->right)
                cg_jump(lEnd);

            cg_label(lFalse);

            // optional ELSE clause
            if (node->right) {
                genASM(node->right, NOREG, node->op);
                free_all_registers();
                cg_label(lEnd);
            }

            return NOREG;
        }

        // generate the code for a while statement
        int genWhile(shared_ptr<ASTNode> node) {
            int lStart = label_id++, lEnd = label_id++;
            cg_label(lStart);

            // generate the condition code followed by a jump to the end label
            genASM(node->left, lEnd, node->op);
            free_all_registers();

            // generate the command statement for the body
            genASM(node->right, NOREG, node->op);
            free_all_registers();

            // finally output the jump back to the condition
            cg_jump(lStart);
            cg_label(lEnd);
            return NOREG;
        }

        // add a global symbol to the symbol table
        inline int addglob(string name, int type, int stype) {
            // if symbol's already in symbol table
            int y = findglob(name);
            if (y != -1)
                error_exit("Redeclaration of", name);

            // otherwise, get a new slot
            y = n_globs++;
            Gsym[y] = SymTableStructure(name, type, stype);
            return y;
        }

        // find if a glob exists
        inline int findglob(string name) {
            for (auto it = Gsym.begin(); it != Gsym.end(); ++it) {
                if (it->second.name == name)
                    return it->first;
            }
            return -1;
        }

        // allocate a ree register
        int alloc_register() {
            for (int i = 0; i < 4; i++) {
                if (freereg[i]) {
                    freereg[i] = 0;
                    return i;
                }
            }
            cerr << "Out of registers :(" << endl;
            exit(1);
        }

        // free a register
        void free_register(int reg) {
            if (freereg[reg] != 0)
                error_exit("Error trying to free register", reg);
            freereg[reg] = 1;
        }

        // free all registers
        void free_all_registers() {
            freereg[0] = freereg[1] = freereg[2] = freereg[3] = 1;
        }

        // Print out the assembly preamble
        void cg_preamble() {
            outputFile <<   "\t.text\n"
                            ".LC0:\n"
                            "\t.string\t\"%d\\n\"\n"
                            "printint:\n"
                            "\tpushq\t%rbp\n"
                            "\tmovq\t%rsp, %rbp\n"
                            "\tsubq\t$16, %rsp\n"
                            "\tmovl\t%edi, -4(%rbp)\n"
                            "\tmovl\t-4(%rbp), %eax\n"
                            "\tmovl\t%eax, %esi\n"
                            "\tleaq	.LC0(%rip), %rdi\n"
                            "\tmovl	$0, %eax\n"
                            "\tcall	printf@PLT\n"
                            "\tnop\n"
                            "\tleave\n"
                            "\tret\n"
                            "\n";
        }

        // Print out the assembly postamble
        void cg_postamble() {
            outputFile << 	"\tmovl	$0, %eax\n"
	                        "\tpopq	%rbp\n"
	                        "\tret\n";
        }

        int cg_add(int r1, int r2) {
            outputFile << "\taddq\t" << reglist[r1] << ", " << reglist[r2] << "\n";
            free_register(r1);
            return r2;
        }

        int cg_sub(int r1, int r2) {
            outputFile << "\tsubq\t" << reglist[r2] << ", " << reglist[r1] << "\n";
            free_register(r2);
            return r1;
        }

        int cg_mul(int r1, int r2) {
            outputFile << "\timulq\t" << reglist[r1] << ", " << reglist[r2] << "\n";
            free_register(r1);
            return r2;
        }

        int cg_div(int r1, int r2) {
            outputFile << "\tmovq\t" << reglist[r1] << ", %rax\n";
            outputFile << "\tcqo\n";
            outputFile << "\tidivq\t" << reglist[r2] << "\n";
            outputFile << "\tmovq\t%rax, " << reglist[r1] << "\n";
            free_register(r2);
            return r1;
        }

        // load an integer literal value into a register
        int cg_load(int value) {
            int r = alloc_register(); // allocate a free register
            outputFile << "\tmovq\t$" << value << ", " << reglist[r] << "\n";
            return r;
        }

        // load a value from a variable into a register
        int cg_load_glob(int id) {
            int r = alloc_register();

            if (Gsym[id].type == P_INT)
                outputFile << "\tmovq\t" << Gsym[id].name << "(\%rip), " << reglist[r] << "\n";
            else
                outputFile << "\tmovzbq\t" << Gsym[id].name << "(\%rip), " << reglist[r] << "\n";
            return r;
        }

        // store a register's value into a register
        int cg_store_glob(int r, int id) {
            if (Gsym[id].type == P_INT)
                outputFile << "\tmovq\t" << reglist[r] << ", " << Gsym[id].name << "(\%rip)\n";
            else
                outputFile << "\tmovb\t" << breglist[r] << ", " << Gsym[id].name << "(\%rip)\n";
            return r;
        }

        // call printint with a certain register
        void cg_printint(int r) {
            outputFile << "\tmovq\t" << reglist[r] << ", %rdi\n";
            outputFile << "\tcall\tprintint\n";
            free_register(r);
        }

        // generate a global symbol
        void cg_globsym(int id) {
            // choose P_INT or P_CHAR
            if (Gsym[id].type == P_INT)
                outputFile << "\t.comm\t" << Gsym[id].name << ",8,8\n";
            else
                outputFile << "\t.comm\t" << Gsym[id].name << ",1,1\n";
        }

        // compare two registers and set if true
        int cg_compare_and_set(int ASTop, int r1, int r2) {
            // check the range of the AST operation
            if (ASTop < A_EQ || ASTop > A_GE)
                error_exit("Bad ASTop in cgcompare_and_set()", "");
            outputFile << "\tcmpq\t" << reglist[r2] << ", " << reglist[r1] << "\n";
            outputFile << "\t" << cmplist[ASTop - A_EQ] << "\t" << breglist[r2] << "\n";
            outputFile << "\tmovzbq\t" << breglist[r2] << ", " << reglist[r2] << "\n";
            free_register(r1);
            return r2;
        }

        // compare two registers and jump if false
        int cg_compare_and_jump(int ASTop, int r1, int r2, int label) {
            // check the range of the AST operation
            if (ASTop < A_EQ || ASTop > A_GE)
                error_exit("Bad ASTop in cg_compare_and_jump()", "");
            outputFile << "\tcmpq\t" << reglist[r2] << ", " << reglist[r1] << "\n";
            outputFile << "\t" << invcmplist[ASTop - A_EQ] << "\tL" << label << "\n";
            free_all_registers();
            return NOREG;
        }

        // generate a label
        void cg_label(int l) {
            outputFile << "L" << l << ":\n";
        }

        // generate a jump to a label
        void cg_jump(int l) {
            outputFile << "\tjmp\tL" << l << "\n";
        }

        void cg_func_preamble(string name) {
            outputFile << "\t.text\n\t.globl\t" << name << "\n\t.type\t" << name << ", @function\n" << name << ":\n\tpushq\t%rbp\n\tmovq\t%rsp, %rbp\n";
        }

        void cg_func_postamble() {
            outputFile << "\tmovl $0, %eax\n\tpopq\t%rbp\n\tret\n";
        }

        int cg_widen(int r, int oldType, int newType) {
            return r; // nothing to do
        }


        /* debugging */

        void traverseAST() {
            root->traverse();
            cout << endl;
        }

        template <typename T>
        inline void error_exit(string err_msg, T extra) {
            cerr << err_msg << " " << extra << " on line " << n_line << ":" << line_pos << endl;

            // delete created ASM output file
            int len = outputPath.length();
            char outputPath2[len + 1];
            for (int i = 0; i < len; i++) {
                outputPath2[i] = outputPath[i];
            }

            outputPath2[len] = '\0';
            remove(outputPath2);

            handler(NOSEGINT);
        }

        void print_symbol_table() {
            for (auto it = Gsym.begin(); it != Gsym.end(); ++it)
                cout << it->first << " " << it->second.name << "\n";
        }
    
    private:
        // parsing & scanning stuff
        char c;
        int n_line = 1, line_pos = 0, ident_lim = IDENT_LIM;
        ifstream inputFile;
        string inputPath, filename;
        shared_ptr<ASTNode> root;
        Token t = Token();
        char buf[IDENT_BUFFER_LEN];

        // code generation stuff
        ofstream outputFile;
        string outputPath;
        int freereg[4] = {1, 1, 1, 1};
        int n_globs = 0; // number of globals
        int label_id = 1; // label numbers
        const string reglist[4] = {"%r8", "%r9", "%r10", "%r11"};
        const string breglist[4] = { "%r8b", "%r9b", "%r10b", "%r11b" };
        const string cmplist[6] = {"sete", "setne", "setl", "setg", "setle", "setge"};
        // list of inverted jump instructions in AST order: A_EQ, A_NE, A_LT, A_GT, A_LE, A_GE
        const string invcmplist[6] = {"jne", "je", "jge", "jle", "jg", "jl"};
        map<int, SymTableStructure> Gsym; // store global variables
};

int main(int argc, char** argv) {
    if (argc != 2) {
        cerr << "Usage: " << argv[0] << " infile\n";
        exit(1);
    }

    // listen for segfaults
    signal(SIGSEGV, handler);

    Compiler compiler(argv[1]);
    // compiler.print_symbol_table();
    // cout << compiler.label_id << endl;
    // compiler.print_symbol_table();
    // compiler.traverseAST();
    // compiler.generateAssembly();

    return 0;
}