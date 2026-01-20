"""SQL safety rules and validation logic"""
from typing import List, Tuple
import sqlglot
import logging

logger = logging.getLogger(__name__)

class SQLSafetyRules:
    """Defines and enforces SQL safety rules"""
    
    MAX_LIMIT = 10000
    MAX_JOINS = 3
    
    ALLOWED_STATEMENTS = {"SELECT"}
    
    FORBIDDEN_KEYWORDS = {
        "DELETE", "DROP", "TRUNCATE", "INSERT", "UPDATE",
        "CREATE", "ALTER", "GRANT", "REVOKE", "EXECUTE",
        "EXEC", "CALL"
    }
    
    FORBIDDEN_TABLES = {
        "pg_", "information_schema", "pg_catalog"
    }
    
    @staticmethod
    def validate_query(sql: str) -> Tuple[bool, List[str]]:
        """
        Validate SQL query against safety rules
        
        Returns:
            (is_valid, list_of_errors)
        """
        errors = []
        
        try:
            # Parse SQL with sqlglot
            parsed = sqlglot.parse_one(sql, read="postgres")
            
            # Rule 1: Must be SELECT
            if not isinstance(parsed, sqlglot.exp.Select):
                errors.append("Only SELECT queries are allowed")
                return False, errors
            
            # Rule 2: Must have LIMIT
            if not parsed.args.get("limit"):
                errors.append("Query must include a LIMIT clause")
            else:
                limit_value = parsed.args["limit"].this
                if hasattr(limit_value, "this"):
                    limit_num = int(limit_value.this)
                    if limit_num > SQLSafetyRules.MAX_LIMIT:
                        errors.append(f"LIMIT cannot exceed {SQLSafetyRules.MAX_LIMIT}")
            
            # Rule 3: Check for forbidden keywords in raw SQL
            sql_upper = sql.upper()
            for keyword in SQLSafetyRules.FORBIDDEN_KEYWORDS:
                if keyword in sql_upper:
                    errors.append(f"Forbidden keyword detected: {keyword}")
            
            # Rule 4: Count joins
            joins = list(parsed.find_all(sqlglot.exp.Join))
            if len(joins) > SQLSafetyRules.MAX_JOINS:
                errors.append(f"Too many joins: {len(joins)} (max: {SQLSafetyRules.MAX_JOINS})")
            
            # Rule 5: Check table names
            tables = [table.name for table in parsed.find_all(sqlglot.exp.Table)]
            for table in tables:
                if any(table.lower().startswith(prefix) for prefix in SQLSafetyRules.FORBIDDEN_TABLES):
                    errors.append(f"Access to system table forbidden: {table}")
            
            # Rule 6: No subqueries in FROM (for now - can relax later)
            for from_clause in parsed.find_all(sqlglot.exp.From):
                if from_clause.this and isinstance(from_clause.this, sqlglot.exp.Subquery):
                    errors.append("Subqueries in FROM clause not allowed")
            
            is_valid = len(errors) == 0
            
            if is_valid:
                logger.info(f"SQL validation passed: {sql[:100]}...")
            else:
                logger.warning(f"SQL validation failed: {errors}")
            
            return is_valid, errors
            
        except Exception as e:
            logger.error(f"SQL parsing error: {e}")
            errors.append(f"SQL syntax error: {str(e)}")
            return False, errors