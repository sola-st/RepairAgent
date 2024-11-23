from antlr4 import FileStream, CommonTokenStream
from JavaLexer import JavaLexer
from JavaParser import JavaParser
from JavaListener import JavaListener
from antlr4 import ParseTreeWalker

class FunctionExtractor(JavaListener):
    def __init__(self):
        self.matched_methods = []
        self.target_name = "getLegacyOutputCharset"

    def enterMethodDeclaration(self, ctx):
        try:
            method_name = ctx.Identifier().getText()
            method_body = ctx.methodBody().getText()
            method_params = ctx.formalParameters().getText()
            start_index = (ctx.start.line, ctx.start.column)
            end_index = (ctx.stop.line, ctx.stop.column)
            if method_name == self.target_name:
                self.matched_methods.append((method_name, method_body, method_params, start_index, end_index))
        except Exception as e:
            print(e)

if __name__ == "__main__":
    file_path = "auto_gpt_workspace/closure_10_buggy/src/com/google/javascript/jscomp/AbstractCommandLineRunner.java"
    input_stream = FileStream(file_path)
    
    lexer = JavaLexer(input_stream)
    token_stream = CommonTokenStream(lexer)
    parser = JavaParser(token_stream)
    
    tree = parser.compilationUnit()
    
    extractor = FunctionExtractor()
    walker = ParseTreeWalker()
    walker.walk(extractor, tree)
    print(extractor.matched_methods[0])
