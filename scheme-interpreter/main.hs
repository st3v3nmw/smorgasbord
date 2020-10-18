module Main where
import Control.Monad
import System.Environment
import Text.ParserCombinators.Parsec hiding (spaces)

-- Data structure that can hold any List value
data LispVal = Atom String
             | List [LispVal]
             | DottedList [LispVal] LispVal
             | Number Integer
             | String String
             | Bool Bool

-- recognizes one of the symbols allowed in Scheme identifiers
symbol :: Parser Char
symbol = oneOf "!$%&|*+-/:<=?>@^_~#"

-- skip an arbitrary number of spaces
spaces :: Parser()
spaces = skipMany1 space

readExpr :: String -> String
readExpr input = case parse parseExpr "lisp" input of -- lisp is the name of the parser
    Left err -> "No match: " ++ show err
    Right val -> "Found value"

parseString :: Parser LispVal
parseString = do
                char '"'
                x <- many (noneOf "\"")
                char '"'
                return $ String x

parseAtom :: Parser LispVal
parseAtom = do
                first <- letter <|> symbol
                rest <- many(letter <|> digit <|> symbol)
                let atom = [first] ++ rest
                return $ case atom of
                    "#t" -> Bool True
                    "#f" -> Bool False
                    otherwise -> Atom atom

parseNumber :: Parser LispVal
parseNumber = liftM (Number . read) $ many1 digit

parseExpr :: Parser LispVal
parseExpr = parseAtom
            <|> parseString
            <|> parseNumber

main::IO()
main = do
        args <- getArgs
        putStrLn (readExpr (args !! 0))