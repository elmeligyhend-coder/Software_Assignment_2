package com.finance; 
import java.sql.*;

public class DatabaseManager {
    private static final String URL = "jdbc:sqlite:finance_tracker.db";

    public static Connection connect() throws SQLException {
        return DriverManager.getConnection(URL);
    }

    public static void initialize() {
        String userTable = "CREATE TABLE IF NOT EXISTS users ("
                + "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                + "name TEXT NOT NULL,"
                + "email TEXT UNIQUE NOT NULL,"
                + "password TEXT NOT NULL);";

        String transactionTable = "CREATE TABLE IF NOT EXISTS transactions ("
                + "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                + "user_id INTEGER,"
                + "amount REAL NOT NULL,"
                + "category TEXT,"
                + "date TEXT,"
                + "FOREIGN KEY(user_id) REFERENCES users(id));";

        try (Connection conn = connect(); Statement stmt = conn.createStatement()) {
            stmt.execute(userTable);
            stmt.execute(transactionTable);
            System.out.println("Database Initialized Successfully!");
        } catch (SQLException e) {
            System.out.println("Error initializing DB: " + e.getMessage());
        }
    }
}