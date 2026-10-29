package com.example.accounts.cases;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;

public interface CaseCommentRepository extends JpaRepository<CaseComment, Long> {

    List<CaseComment> findByCaseIdOrderByCreatedAtAsc(String caseId);
}
