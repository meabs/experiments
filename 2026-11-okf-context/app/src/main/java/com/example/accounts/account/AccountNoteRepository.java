package com.example.accounts.account;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;

public interface AccountNoteRepository extends JpaRepository<AccountNote, Long> {

    List<AccountNote> findByAccountIdOrderByCreatedAtDesc(Long accountId);
}
